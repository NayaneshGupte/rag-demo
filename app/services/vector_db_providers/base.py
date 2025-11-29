"""
Abstract base class for vector database providers.
Defines the interface that all vector DB implementations must follow.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class VectorDBResponse:
    """Standardized response from vector DB operations."""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    metadata: Optional[Dict] = None


class VectorDBProvider(ABC):
    """Abstract base class for vector database providers.
    
    All vector DB implementations (Pinecone, Weaviate, Chroma, etc.)
    must inherit from this class and implement all abstract methods.
    """
    
    @abstractmethod
    def validate_credentials(self) -> bool:
        """
        Validate that provider has valid credentials and can connect.
        
        Returns:
            bool: True if credentials valid and connection possible, False otherwise
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if provider is available and operational.
        
        Returns:
            bool: True if provider is operational, False otherwise
        """
        pass
    
    @abstractmethod
    def initialize(self) -> bool:
        """
        Initialize the vector DB provider.
        Sets up connections, indexes, etc.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get_or_create_index(self, index_name: str, dimension: Optional[int] = None) -> bool:
        """
        Get existing index or create new one.
        
        Args:
            index_name: Name of the index
            dimension: Dimension for embeddings (required for creation)
            
        Returns:
            bool: True if index exists or created successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def add_documents(self, documents: List[Dict], index_name: str) -> VectorDBResponse:
        """
        Add documents to vector store with embeddings.
        
        Args:
            documents: List of documents with page_content and metadata
            index_name: Name of the index
            
        Returns:
            VectorDBResponse: Response with success status and count added
        """
        pass
    
    @abstractmethod
    def similarity_search(self, query: str, k: int = 3, index_name: Optional[str] = None) -> VectorDBResponse:
        """
        Search for similar documents.
        
        Args:
            query: Query text
            k: Number of results to return
            index_name: Name of the index (uses default if None)
            
        Returns:
            VectorDBResponse: Response with list of similar documents
        """
        pass
    
    @abstractmethod
    def get_index_stats(self, index_name: Optional[str] = None) -> VectorDBResponse:
        """
        Get statistics about the index.
        
        Args:
            index_name: Name of the index (uses default if None)
            
        Returns:
            VectorDBResponse: Response with index statistics
        """
        pass
    
    @abstractmethod
    def list_documents(self, index_name: Optional[str] = None, limit: int = 10,
                      pagination_token: Optional[str] = None) -> VectorDBResponse:
        """
        List documents in the index.
        
        Args:
            index_name: Name of the index (uses default if None)
            limit: Maximum number of documents to return
            pagination_token: Token for paginated results
            
        Returns:
            VectorDBResponse: Response with list of documents and next token
        """
        pass
    
    @abstractmethod
    def delete_document(self, document_id: str, index_name: Optional[str] = None) -> VectorDBResponse:
        """
        Delete a document from the index.
        
        Args:
            document_id: ID of document to delete
            index_name: Name of the index (uses default if None)
            
        Returns:
            VectorDBResponse: Response with success status
        """
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """
        Get name of the provider.
        
        Returns:
            str: Provider name (e.g., 'pinecone', 'weaviate', 'chroma')
        """
        pass
    
    @abstractmethod
    def get_provider_status(self) -> Dict[str, Any]:
        """
        Get status information about the provider.
        
        Returns:
            Dict: Status information including version, available indexes, etc.
        """
        pass
