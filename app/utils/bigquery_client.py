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
    
    def get_schema_info(self, table_name: str) -> Dict[str, Any]:
        """
        Get schema information for a table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            Schema information
        """
        try:
            table_id = f"{settings.google_cloud_project}.{self.dataset}.{table_name}"
            table = self.client.get_table(table_id)
            
            schema_info = {
                "table_name": table_name,
                "columns": [],
                "row_count": table.num_rows,
                "size_bytes": table.num_bytes,
                "created": table.created.isoformat() if table.created else None,
                "modified": table.modified.isoformat() if table.modified else None
            }
            
            for field in table.schema:
                schema_info["columns"].append({
                    "name": field.name,
                    "type": field.field_type,
                    "mode": field.mode,
                    "description": field.description
                })
            
            return schema_info
            
        except GoogleCloudError as e:
            logger.error("Failed to get schema info", table_name=table_name, error=str(e))
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
