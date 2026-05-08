"""
Shared temporary session storage.

Both the monolith (rag_system.api) and the query microservice import from here.
Do not import from rag_system.api.* in this module.
"""
from rag_system.api.temp_storage import TempIndexManager, temp_index_manager

__all__ = ["TempIndexManager", "temp_index_manager"]
