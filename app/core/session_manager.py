"""
Session management for user conversations and context.
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from collections import defaultdict

from app.models.agent import AgentContext
from app.utils.logger import get_logger

logger = get_logger(__name__)


class SessionManager:
    """Manages user sessions and conversation context."""
    
    def __init__(self):
        """Initialize session manager."""
        self.sessions: Dict[str, AgentContext] = {}
        self.session_metadata: Dict[str, Dict[str, Any]] = {}
        self.session_timeout = timedelta(hours=24)  # 24 hour timeout
    
    def create_session(self, user_id: Optional[str] = None) -> str:
        """
        Create a new session.
        
        Args:
            user_id: Optional user identifier
            
        Returns:
            Session ID
        """
        session_id = str(uuid.uuid4())
        
        self.sessions[session_id] = AgentContext(
            session_id=session_id,
            user_id=user_id,
            conversation_history=[],
            schema_info=None,
            user_preferences={},
            context_variables={}
        )
        
        self.session_metadata[session_id] = {
            "created_at": datetime.utcnow(),
            "last_activity": datetime.utcnow(),
            "user_id": user_id
        }
        
        logger.info("Created new session", session_id=session_id, user_id=user_id)
        return session_id
    
    def get_session(self, session_id: str) -> Optional[AgentContext]:
        """
        Get session context.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session context or None if not found
        """
        if session_id not in self.sessions:
            return None
        
        # Update last activity
        if session_id in self.session_metadata:
            self.session_metadata[session_id]["last_activity"] = datetime.utcnow()
        
        return self.sessions[session_id]
    
    def update_session(self, session_id: str, **kwargs) -> bool:
        """
        Update session context.
        
        Args:
            session_id: Session identifier
            **kwargs: Fields to update
            
        Returns:
            True if updated successfully
        """
        if session_id not in self.sessions:
            return False
        
        session = self.sessions[session_id]
        
        for key, value in kwargs.items():
            if hasattr(session, key):
                setattr(session, key, value)
        
        # Update last activity
        if session_id in self.session_metadata:
            self.session_metadata[session_id]["last_activity"] = datetime.utcnow()
        
        logger.debug("Updated session", session_id=session_id, updates=kwargs)
        return True
    
    def add_message_to_history(self, session_id: str, role: str, content: str) -> bool:
        """
        Add a message to the conversation history.
        
        Args:
            session_id: Session identifier
            role: Message role (user/assistant)
            content: Message content
            
        Returns:
            True if added successfully
        """
        if session_id not in self.sessions:
            return False
        
        session = self.sessions[session_id]
        session.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Update last activity
        if session_id in self.session_metadata:
            self.session_metadata[session_id]["last_activity"] = datetime.utcnow()
        
        logger.debug("Added message to history", session_id=session_id, role=role)
        return True
    
    def get_conversation_history(self, session_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get conversation history for a session.
        
        Args:
            session_id: Session identifier
            limit: Maximum number of messages to return
            
        Returns:
            List of conversation messages
        """
        if session_id not in self.sessions:
            return []
        
        history = self.sessions[session_id].conversation_history
        
        if limit:
            history = history[-limit:]
        
        return history
    
    def update_schema_info(self, session_id: str, schema_info: Dict[str, Any]) -> bool:
        """
        Update schema information for a session.
        
        Args:
            session_id: Session identifier
            schema_info: Database schema information
            
        Returns:
            True if updated successfully
        """
        return self.update_session(session_id, schema_info=schema_info)
    
    def update_user_preferences(self, session_id: str, preferences: Dict[str, Any]) -> bool:
        """
        Update user preferences for a session.
        
        Args:
            session_id: Session identifier
            preferences: User preferences
            
        Returns:
            True if updated successfully
        """
        if session_id not in self.sessions:
            return False
        
        session = self.sessions[session_id]
        session.user_preferences.update(preferences)
        
        # Update last activity
        if session_id in self.session_metadata:
            self.session_metadata[session_id]["last_activity"] = datetime.utcnow()
        
        return True
    
    def set_context_variable(self, session_id: str, key: str, value: Any) -> bool:
        """
        Set a context variable for a session.
        
        Args:
            session_id: Session identifier
            key: Variable key
            value: Variable value
            
        Returns:
            True if set successfully
        """
        if session_id not in self.sessions:
            return False
        
        session = self.sessions[session_id]
        session.context_variables[key] = value
        
        # Update last activity
        if session_id in self.session_metadata:
            self.session_metadata[session_id]["last_activity"] = datetime.utcnow()
        
        return True
    
    def get_context_variable(self, session_id: str, key: str) -> Optional[Any]:
        """
        Get a context variable for a session.
        
        Args:
            session_id: Session identifier
            key: Variable key
            
        Returns:
            Variable value or None if not found
        """
        if session_id not in self.sessions:
            return None
        
        session = self.sessions[session_id]
        return session.context_variables.get(key)
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if deleted successfully
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
        
        if session_id in self.session_metadata:
            del self.session_metadata[session_id]
        
        logger.info("Deleted session", session_id=session_id)
        return True
    
    def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions.
        
        Returns:
            Number of sessions cleaned up
        """
        now = datetime.utcnow()
        expired_sessions = []
        
        for session_id, metadata in self.session_metadata.items():
            if now - metadata["last_activity"] > self.session_timeout:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            self.delete_session(session_id)
        
        if expired_sessions:
            logger.info("Cleaned up expired sessions", count=len(expired_sessions))
        
        return len(expired_sessions)
    
    def get_session_stats(self) -> Dict[str, Any]:
        """
        Get session statistics.
        
        Returns:
            Session statistics
        """
        total_sessions = len(self.sessions)
        active_sessions = 0
        total_messages = 0
        
        for session_id, session in self.sessions.items():
            if session_id in self.session_metadata:
                metadata = self.session_metadata[session_id]
                if datetime.utcnow() - metadata["last_activity"] < timedelta(hours=1):
                    active_sessions += 1
            
            total_messages += len(session.conversation_history)
        
        return {
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "total_messages": total_messages,
            "session_timeout_hours": self.session_timeout.total_seconds() / 3600
        }


# Global session manager instance
session_manager = SessionManager()

