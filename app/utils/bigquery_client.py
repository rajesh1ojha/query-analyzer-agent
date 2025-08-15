"""
BigQuery client utility for database operations.
"""

import time
from typing import List, Dict, Any, Optional, Tuple
from google.cloud import bigquery
from google.cloud.exceptions import GoogleCloudError
from app.config.settings import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class BigQueryClient:
    """BigQuery client for executing queries and managing data."""
    
    def __init__(self):
        """Initialize BigQuery client."""
        self.client = bigquery.Client(project=settings.google_cloud_project)
        self.dataset = settings.bigquery_dataset
        self.max_results = settings.bigquery_max_results
        self.timeout = settings.bigquery_timeout_seconds
        
    def execute_query(self, query: str, params: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Execute a BigQuery SQL query.
        
        Args:
            query: SQL query to execute
            params: Query parameters (optional)
            
        Returns:
            Query results and metadata
        """
        start_time = time.time()
        
        try:
            # Configure query job
            job_config = bigquery.QueryJobConfig(
                query_parameters=params,
                maximum_bytes_billed=10 * 1024 * 1024 * 1024,  # 10GB
                use_query_cache=True
            )
            
            # Execute query
            query_job = self.client.query(query, job_config=job_config)
            
            # Wait for completion
            query_job.result(timeout=self.timeout)
            
            # Get results
            results = []
            for row in query_job:
                results.append(dict(row.items()))
            
            execution_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            return {
                "success": True,
                "data": results,
                "row_count": len(results),
                "execution_time_ms": execution_time,
                "total_bytes_processed": query_job.total_bytes_processed,
                "total_bytes_billed": query_job.total_bytes_billed,
                "job_id": query_job.job_id
            }
            
        except GoogleCloudError as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error("BigQuery query execution failed", 
                        query=query, error=str(e), execution_time_ms=execution_time)
            
            return {
                "success": False,
                "error": str(e),
                "execution_time_ms": execution_time,
                "data": [],
                "row_count": 0
            }
    
    def get_comprehensive_schema_info(self, table_names: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get comprehensive schema information from INFORMATION_SCHEMA.COLUMN_FIELD_PATHS.
        
        Args:
            table_names: Optional list of specific table names to fetch schema for
            
        Returns:
            Comprehensive schema information including table, column, data type, and description
        """
        try:
            # Build the query to get comprehensive schema information
            if table_names:
                table_filter = "', '".join(table_names)
                where_clause = f"WHERE table_name IN ('{table_filter}')"
            else:
                where_clause = ""
            
            query = f"""
            SELECT 
                table_name,
                column_name,
                data_type,
                is_nullable,
                column_default,
                description,
                ordinal_position,
                is_partitioning_column,
                clustering_fields
            FROM `{settings.google_cloud_project}.{self.dataset}.INFORMATION_SCHEMA.COLUMN_FIELD_PATHS`
            {where_clause}
            ORDER BY table_name, ordinal_position
            """
            
            result = self.execute_query(query)
            
            if not result["success"]:
                logger.error("Failed to fetch comprehensive schema info", error=result.get("error"))
                return {"error": result.get("error")}
            
            # Organize schema information by table
            schema_info = {
                "project": settings.google_cloud_project,
                "dataset": self.dataset,
                "tables": {},
                "total_tables": 0,
                "total_columns": 0,
                "fetched_at": time.time()
            }
            
            for row in result["data"]:
                table_name = row["table_name"]
                column_name = row["column_name"]
                
                if table_name not in schema_info["tables"]:
                    schema_info["tables"][table_name] = {
                        "table_name": table_name,
                        "columns": {},
                        "column_count": 0,
                        "partitioning_column": None,
                        "clustering_fields": []
                    }
                
                schema_info["tables"][table_name]["columns"][column_name] = {
                    "column_name": column_name,
                    "data_type": row["data_type"],
                    "is_nullable": row["is_nullable"] == "YES",
                    "column_default": row["column_default"],
                    "description": row["description"] or "",
                    "ordinal_position": row["ordinal_position"],
                    "is_partitioning_column": row["is_partitioning_column"] == "YES",
                    "clustering_fields": row["clustering_fields"] or []
                }
                
                schema_info["tables"][table_name]["column_count"] += 1
                schema_info["total_columns"] += 1
                
                # Track partitioning and clustering info
                if row["is_partitioning_column"] == "YES":
                    schema_info["tables"][table_name]["partitioning_column"] = column_name
                
                if row["clustering_fields"]:
                    schema_info["tables"][table_name]["clustering_fields"] = row["clustering_fields"]
            
            schema_info["total_tables"] = len(schema_info["tables"])
            
            logger.info("Comprehensive schema info fetched", 
                       tables_count=schema_info["total_tables"], 
                       columns_count=schema_info["total_columns"])
            
            return schema_info
            
        except Exception as e:
            logger.error("Failed to get comprehensive schema info", error=str(e))
            return {"error": str(e)}
    
    def get_table_schema_summary(self, table_names: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get a summary of table schemas for LLM context.
        
        Args:
            table_names: Optional list of specific table names
            
        Returns:
            Schema summary optimized for LLM prompts
        """
        comprehensive_schema = self.get_comprehensive_schema_info(table_names)
        
        if "error" in comprehensive_schema:
            return comprehensive_schema
        
        # Create a simplified summary for LLM context
        schema_summary = {
            "project": comprehensive_schema["project"],
            "dataset": comprehensive_schema["dataset"],
            "tables": {}
        }
        
        for table_name, table_info in comprehensive_schema["tables"].items():
            schema_summary["tables"][table_name] = {
                "table_name": table_name,
                "column_count": table_info["column_count"],
                "columns": []
            }
            
            # Add column information in a format suitable for LLM prompts
            for col_name, col_info in table_info["columns"].items():
                column_desc = {
                    "name": col_name,
                    "type": col_info["data_type"],
                    "description": col_info["description"] or f"{col_info['data_type']} column",
                    "nullable": col_info["is_nullable"],
                    "default": col_info["column_default"]
                }
                
                # Add special indicators
                if col_info["is_partitioning_column"]:
                    column_desc["description"] += " (partitioning column)"
                
                schema_summary["tables"][table_name]["columns"].append(column_desc)
        
        return schema_summary
    
    def get_schema_info(self, table_name: str) -> Dict[str, Any]:
        """
        Get schema information for a specific table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            Schema information
        """
        comprehensive_schema = self.get_comprehensive_schema_info([table_name])
        
        if "error" in comprehensive_schema:
            # Fallback to basic schema info
            return self._get_basic_schema_info(table_name)
        
        if table_name in comprehensive_schema["tables"]:
            return comprehensive_schema["tables"][table_name]
        else:
            return {"error": f"Table {table_name} not found"}
    
    def _get_basic_schema_info(self, table_name: str) -> Dict[str, Any]:
        """
        Fallback method to get basic schema information using BigQuery API.
        
        Args:
            table_name: Name of the table
            
        Returns:
            Basic schema information
        """
        try:
            table_id = f"{settings.google_cloud_project}.{self.dataset}.{table_name}"
            table = self.client.get_table(table_id)
            
            schema_info = {
                "table_name": table_name,
                "columns": {},
                "column_count": len(table.schema),
                "row_count": table.num_rows,
                "size_bytes": table.num_bytes,
                "created": table.created.isoformat() if table.created else None,
                "modified": table.modified.isoformat() if table.modified else None
            }
            
            for field in table.schema:
                schema_info["columns"][field.name] = {
                    "column_name": field.name,
                    "data_type": field.field_type,
                    "mode": field.mode,
                    "description": field.description or f"{field.field_type} column",
                    "nullable": field.mode == "NULLABLE"
                }
            
            return schema_info
            
        except GoogleCloudError as e:
            logger.error("Failed to get basic schema info", table_name=table_name, error=str(e))
            return {"error": str(e)}
    
    def list_tables(self) -> List[str]:
        """
        List all tables in the dataset.
        
        Returns:
            List of table names
        """
        try:
            dataset_ref = self.client.dataset(self.dataset)
            tables = list(self.client.list_tables(dataset_ref))
            return [table.table_id for table in tables]
            
        except GoogleCloudError as e:
            logger.error("Failed to list tables", error=str(e))
            return []
    
    def get_table_metadata(self, table_names: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get comprehensive table metadata including row counts, sizes, and creation dates.
        
        Args:
            table_names: Optional list of specific table names
            
        Returns:
            Table metadata
        """
        try:
            if table_names:
                table_filter = "', '".join(table_names)
                where_clause = f"WHERE table_name IN ('{table_filter}')"
            else:
                where_clause = ""
            
            query = f"""
            SELECT 
                table_name,
                table_type,
                creation_time,
                last_modified_time,
                row_count,
                size_bytes,
                description
            FROM `{settings.google_cloud_project}.{self.dataset}.INFORMATION_SCHEMA.TABLES`
            {where_clause}
            ORDER BY table_name
            """
            
            result = self.execute_query(query)
            
            if not result["success"]:
                return {"error": result.get("error")}
            
            metadata = {
                "project": settings.google_cloud_project,
                "dataset": self.dataset,
                "tables": {}
            }
            
            for row in result["data"]:
                table_name = row["table_name"]
                metadata["tables"][table_name] = {
                    "table_name": table_name,
                    "table_type": row["table_type"],
                    "creation_time": row["creation_time"],
                    "last_modified_time": row["last_modified_time"],
                    "row_count": row["row_count"],
                    "size_bytes": row["size_bytes"],
                    "size_mb": row["size_bytes"] / (1024 * 1024) if row["size_bytes"] else 0,
                    "description": row["description"] or ""
                }
            
            return metadata
            
        except Exception as e:
            logger.error("Failed to get table metadata", error=str(e))
            return {"error": str(e)}
    
    def validate_query(self, query: str) -> Dict[str, Any]:
        """
        Validate a SQL query without executing it.
        
        Args:
            query: SQL query to validate
            
        Returns:
            Validation result
        """
        try:
            # Create a dry-run query job
            job_config = bigquery.QueryJobConfig(dry_run=True)
            query_job = self.client.query(query, job_config=job_config)
            
            return {
                "valid": True,
                "total_bytes_processed": query_job.total_bytes_processed,
                "total_bytes_billed": query_job.total_bytes_billed,
                "estimated_cost": self._estimate_cost(query_job.total_bytes_billed)
            }
            
        except GoogleCloudError as e:
            return {
                "valid": False,
                "error": str(e)
            }
    
    def _estimate_cost(self, bytes_billed: int) -> float:
        """Estimate query cost based on bytes billed."""
        # BigQuery pricing: $5 per TB scanned
        cost_per_tb = 5.0
        bytes_per_tb = 1024 * 1024 * 1024 * 1024
        return (bytes_billed / bytes_per_tb) * cost_per_tb
    
    def get_table_preview(self, table_name: str, limit: int = 10) -> Dict[str, Any]:
        """
        Get a preview of table data.
        
        Args:
            table_name: Name of the table
            limit: Number of rows to return
            
        Returns:
            Table preview data
        """
        query = f"SELECT * FROM `{settings.google_cloud_project}.{self.dataset}.{table_name}` LIMIT {limit}"
        return self.execute_query(query)
