import time
import uuid
import logging
from threading import Lock
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

SESSION_TTL = 3600  # seconds — sessions expire after 1 hour of inactivity
MAX_SESSIONS = 100  # hard cap to prevent unbounded memory growth


class TempIndexManager:
    """Manage temporary in-memory indexes with TTL-based eviction."""

    def __init__(self) -> None:
        self.temp_indexes: Dict[str, List[Dict[str, Any]]] = {}
        self._last_accessed: Dict[str, float] = {}
        self._lock = Lock()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _evict_expired(self) -> None:
        """Remove expired sessions while the lock is held."""
        now = time.monotonic()
        expired = [sid for sid, ts in self._last_accessed.items() if now - ts > SESSION_TTL]
        for sid in expired:
            self.temp_indexes.pop(sid, None)
            self._last_accessed.pop(sid, None)
            logger.info(f"Evicted expired session {sid}")

    def _evict_oldest(self) -> None:
        """Remove the least recently used session while the lock is held."""
        if not self._last_accessed:
            return
        oldest = min(self._last_accessed, key=lambda k: self._last_accessed[k])
        self.temp_indexes.pop(oldest, None)
        self._last_accessed.pop(oldest, None)
        logger.info(f"Evicted oldest session {oldest} (MAX_SESSIONS={MAX_SESSIONS} reached)")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_temp_index(self, session_id: str, temp_data: Dict[str, Any]) -> None:
        """Add temporary indexed data to a session.

        Args:
            session_id: Session identifier.
            temp_data: Temporary chunks and embeddings payload.
        """
        with self._lock:
            self._evict_expired()
            if session_id not in self.temp_indexes and len(self.temp_indexes) >= MAX_SESSIONS:
                self._evict_oldest()
            if session_id not in self.temp_indexes:
                self.temp_indexes[session_id] = []
            self.temp_indexes[session_id].append(temp_data)
            self._last_accessed[session_id] = time.monotonic()
        logger.info(f"Added temporary index for session {session_id}, total files: {len(self.temp_indexes[session_id])}")

    def get_temp_index(self, session_id: str) -> Optional[List[Dict[str, Any]]]:
        """Return temporary indexed data for a session.

        Args:
            session_id: Session identifier.

        Returns:
            Temporary data list if the session exists, otherwise None.
        """
        with self._lock:
            result = self.temp_indexes.get(session_id)
            if result is not None:
                self._last_accessed[session_id] = time.monotonic()
            return result

    def remove_temp_index(self, session_id: str) -> bool:
        """Remove all temporary indexed data for a session.

        Args:
            session_id: Session identifier.

        Returns:
            True if the session existed and was removed, otherwise False.
        """
        with self._lock:
            if session_id in self.temp_indexes:
                del self.temp_indexes[session_id]
                self._last_accessed.pop(session_id, None)
                logger.info(f"Removed temporary index for session {session_id}")
                return True
            return False

    def remove_temp_file(self, session_id: str, filename: str) -> bool:
        """Remove one temporary file from a session.

        Args:
            session_id: Session identifier.
            filename: Source filename to remove.

        Returns:
            True if a file was removed, otherwise False.
        """
        with self._lock:
            if session_id not in self.temp_indexes:
                return False
            temp_data_list = self.temp_indexes[session_id]
            initial_length = len(temp_data_list)
            self.temp_indexes[session_id] = [
                td for td in temp_data_list
                if not (td.get('chunks') and
                        len(td['chunks']) > 0 and
                        isinstance(td['chunks'][0], dict) and
                        td['chunks'][0].get('source') == filename)
            ]
            removed = len(self.temp_indexes[session_id]) < initial_length
            if len(self.temp_indexes[session_id]) == 0:
                del self.temp_indexes[session_id]
                self._last_accessed.pop(session_id, None)
            elif removed:
                self._last_accessed[session_id] = time.monotonic()
        if removed:
            logger.info(f"Removed file '{filename}' from session {session_id}")
        return removed

    def get_temp_file_content(self, session_id: str, filename: str) -> Optional[Dict[str, Any]]:
        """Return temporary indexed data for one session file.

        Args:
            session_id: Session identifier.
            filename: Source filename to find.

        Returns:
            Temporary file payload if found, otherwise None.
        """
        with self._lock:
            if session_id not in self.temp_indexes:
                return None
            self._last_accessed[session_id] = time.monotonic()
            for temp_data in self.temp_indexes[session_id]:
                if (temp_data.get('chunks') and
                        len(temp_data['chunks']) > 0 and
                        isinstance(temp_data['chunks'][0], dict) and
                        temp_data['chunks'][0].get('source') == filename):
                    return temp_data
            return None

    def has_session(self, session_id: str) -> bool:
        """Return whether a temporary session exists.

        Args:
            session_id: Session identifier.

        Returns:
            True if the session exists, otherwise False.
        """
        with self._lock:
            exists = session_id in self.temp_indexes
            if exists:
                self._last_accessed[session_id] = time.monotonic()
            return exists

    def generate_session_id(self) -> str:
        """Generate a new temporary session identifier.

        Returns:
            A UUID string.
        """
        return str(uuid.uuid4())

    def get_all_sessions(self) -> List[str]:
        """Return all active temporary session identifiers.

        Returns:
            Active session identifiers.
        """
        with self._lock:
            return list(self.temp_indexes.keys())

    def clear_all(self) -> None:
        """Remove all temporary sessions and indexes."""
        with self._lock:
            self.temp_indexes.clear()
            self._last_accessed.clear()
        logger.info("Cleared all temporary indexes")


temp_index_manager = TempIndexManager()
