from typing import Dict, List
import uuid
import logging

logger = logging.getLogger(__name__)


class TempIndexManager:
    """Manager for temporary in-memory indexes."""
    
    def __init__(self):
        self.temp_indexes: Dict[str, List] = {}
    
    def add_temp_index(self, session_id: str, temp_data: List) -> None:
        """Add temporary index data for a session."""
        self.temp_indexes[session_id] = temp_data
        logger.info(f"Added temporary index for session {session_id}")
    
    def get_temp_index(self, session_id: str) -> List:
        """Get temporary index data for a session."""
        return self.temp_indexes.get(session_id)
    
    def remove_temp_index(self, session_id: str) -> bool:
        """Remove temporary index data for a session."""
        if session_id in self.temp_indexes:
            del self.temp_indexes[session_id]
            logger.info(f"Removed temporary index for session {session_id}")
            return True
        return False
    
    def has_session(self, session_id: str) -> bool:
        """Check if session exists."""
        return session_id in self.temp_indexes
    
    def generate_session_id(self) -> str:
        """Generate a new session ID."""
        return str(uuid.uuid4())
    
    def get_all_sessions(self) -> List[str]:
        """Get all active session IDs."""
        return list(self.temp_indexes.keys())
    
    def clear_all(self) -> None:
        """Clear all temporary indexes."""
        self.temp_indexes.clear()
        logger.info("Cleared all temporary indexes")


# Глобальный экземпляр менеджера
temp_index_manager = TempIndexManager() 