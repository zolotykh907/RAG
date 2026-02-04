from typing import Dict, List, Optional
import uuid
import logging

logger = logging.getLogger(__name__)


class TempIndexManager:
    """Manager for temporary in-memory indexes."""

    def __init__(self):
        # Changed to store list of files per session
        self.temp_indexes: Dict[str, List[Dict]] = {}

    def add_temp_index(self, session_id: str, temp_data: Dict) -> None:
        """Add temporary index data for a session.

        Args:
            session_id (str): Unique identifier for the session.
            temp_data (Dict): Dictionary with chunks and embeddings.
        """
        if session_id not in self.temp_indexes:
            self.temp_indexes[session_id] = []

        self.temp_indexes[session_id].append(temp_data)
        logger.info(f"Added temporary index for session {session_id}, total files: {len(self.temp_indexes[session_id])}")

    def get_temp_index(self, session_id: str) -> Optional[List[Dict]]:
        """Get all temporary index data for a session.

        Args:
            session_id (str): Unique identifier for the session.

        Returns:
            List[Dict]: List of temporary index data if exists, otherwise None."""
        return self.temp_indexes.get(session_id)

    def remove_temp_index(self, session_id: str) -> bool:
        """Remove all temporary index data for a session.

        Args:
            session_id (str): Unique identifier for the session.

        Returns:
            bool: True if removed, False if session does not exist."""
        if session_id in self.temp_indexes:
            del self.temp_indexes[session_id]
            logger.info(f"Removed temporary index for session {session_id}")
            return True
        return False

    def remove_temp_file(self, session_id: str, filename: str) -> bool:
        """Remove a specific temporary file from a session.

        Args:
            session_id (str): Unique identifier for the session.
            filename (str): Name of the file to remove.

        Returns:
            bool: True if removed, False if file or session does not exist."""
        if session_id not in self.temp_indexes:
            return False

        temp_data_list = self.temp_indexes[session_id]
        initial_length = len(temp_data_list)

        # Remove the file with matching filename
        self.temp_indexes[session_id] = [
            temp_data for temp_data in temp_data_list
            if not (temp_data.get('chunks') and
                   len(temp_data['chunks']) > 0 and
                   isinstance(temp_data['chunks'][0], dict) and
                   temp_data['chunks'][0].get('source') == filename)
        ]

        removed = len(self.temp_indexes[session_id]) < initial_length

        # If no files left, remove the session entry
        if len(self.temp_indexes[session_id]) == 0:
            del self.temp_indexes[session_id]

        if removed:
            logger.info(f"Removed file '{filename}' from session {session_id}")

        return removed

    def get_temp_file_content(self, session_id: str, filename: str) -> Optional[Dict]:
        """Get content of a specific temporary file.

        Args:
            session_id (str): Unique identifier for the session.
            filename (str): Name of the file to retrieve.

        Returns:
            Dict: File content with chunks, or None if not found."""
        if session_id not in self.temp_indexes:
            return None

        temp_data_list = self.temp_indexes[session_id]

        for temp_data in temp_data_list:
            if (temp_data.get('chunks') and
                len(temp_data['chunks']) > 0 and
                isinstance(temp_data['chunks'][0], dict) and
                temp_data['chunks'][0].get('source') == filename):
                return temp_data

        return None

    def has_session(self, session_id: str) -> bool:
        """Check if session exists.

        Args:
            session_id (str): Unique identifier for the session.

        Returns:
            bool: True if session exists, False otherwise."""
        return session_id in self.temp_indexes

    def generate_session_id(self) -> str:
        """Generate a new session ID.

        Returns:
            str: Unique session ID."""
        return str(uuid.uuid4())

    def get_all_sessions(self) -> List[str]:
        """Get all active session IDs.

        Returns:
            List[str]: List of all active session IDs."""
        return list(self.temp_indexes.keys())

    def clear_all(self) -> None:
        """Clear all temporary indexes."""
        self.temp_indexes.clear()
        logger.info("Cleared all temporary indexes")


temp_index_manager = TempIndexManager()
