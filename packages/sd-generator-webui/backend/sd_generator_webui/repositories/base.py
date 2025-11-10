"""
Base repository interfaces for data access abstraction.

This module provides abstract base classes that define the contract
for repository implementations. Following the Repository Pattern allows:
- Easy testing with mock implementations
- Swapping storage backends (SQLite → PostgreSQL) without changing business logic
- Clear separation between domain logic and data access
"""

from abc import ABC, abstractmethod
from typing import Dict, Generic, List, Optional, TypeVar

# Generic type for entity
T = TypeVar('T')


class Repository(ABC, Generic[T]):
    """
    Base repository interface for single-entity operations.

    This abstract class defines the minimal contract that all repositories must implement.
    It provides basic CRUD operations for a single entity type.
    """

    @abstractmethod
    def get(self, id: str) -> Optional[T]:
        """
        Get entity by ID.

        Args:
            id: Unique identifier for the entity

        Returns:
            Entity if found, None otherwise
        """
        pass

    @abstractmethod
    def save(self, entity: T) -> None:
        """
        Save entity (insert or update).

        Args:
            entity: Entity to save
        """
        pass

    @abstractmethod
    def delete(self, id: str) -> bool:
        """
        Delete entity by ID.

        Args:
            id: Unique identifier for the entity

        Returns:
            True if entity was deleted, False if not found
        """
        pass


class BatchRepository(Repository[T]):
    """
    Repository interface with batch operations for performance.

    Extends the base Repository with batch operations that allow fetching
    multiple entities in a single database query (vs N queries in a loop).

    This is critical for performance when dealing with large collections
    (e.g., listing 1000+ sessions with stats).
    """

    @abstractmethod
    def get_batch(self, ids: List[str]) -> Dict[str, T]:
        """
        Get multiple entities by IDs in a single query (PERFORMANCE).

        This method MUST be implemented efficiently with a single database query
        (e.g., SELECT * FROM table WHERE id IN (...)) instead of N individual queries.

        Args:
            ids: List of unique identifiers

        Returns:
            Dict mapping ID to entity (missing IDs are not included in result)
        """
        pass

    @abstractmethod
    def list_all(self) -> List[T]:
        """
        List all entities.

        Returns:
            List of all entities (may be empty)
        """
        pass
