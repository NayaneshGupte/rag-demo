"""
Vector store service using pluggable vector database providers.
Provides unified interface to all vector database operations.
"""
import logging
from typing import List, Dict, Optional
from app.config import Config
from app.services.vector_db_providers.factory import VectorDBFactory

logger = logging.getLogger(__name__)


class VectorStoreService:
    """Service for vector store operations using pluggable providers."""
    
    def __init__(self, vector_db_type: Optional[str] = None, 
                 fallback_providers: Optional[List[str]] = None):
        """
        Initialize vector store service.
        
        Args:
            vector_db_type: Primary vector DB type (defaults to Config.VECTOR_DB_TYPE)
            fallback_providers: List of fallback providers (defaults to Config.VECTOR_DB_FALLBACK_PROVIDERS)
        """
        db_type = vector_db_type or Config.VECTOR_DB_TYPE
        fallbacks = fallback_providers or Config.VECTOR_DB_FALLBACK_PROVIDERS
        
        try:
            self.factory = VectorDBFactory(
                primary_provider=db_type,
                fallback_providers=fallbacks
            )
            logger.info(f"VectorStoreService initialized with {db_type} provider")
        except Exception as e:
            logger.error(f"Error initializing VectorStoreService: {e}")
            raise
    
    def get_provider_name(self) -> str:
        """
        Get name of current vector DB provider.
        
        Returns:
            str: Provider name
        """
        provider = self.factory.get_current_provider()
        if provider:
            return provider.get_provider_name()
        return "unknown"
    
    def get_provider_status(self) -> Dict:
        """
        Get status of vector DB providers.
        
        Returns:
            Dict: Status information
        """
        return self.factory.get_provider_status()
    
    def get_or_create_index(self, index_name: Optional[str] = None, 
                           dimension: Optional[int] = None) -> bool:
        """
        Get or create vector index.
        
        Args:
            index_name: Name of index (uses default if None)
            dimension: Dimension for embeddings
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not index_name:
            index_name = Config.PINECONE_INDEX_NAME
        
        return self.factory.get_or_create_index(index_name, dimension)
    
    def add_documents(self, documents: List[Dict], 
                     index_name: Optional[str] = None) -> int:
        """
        Add documents to vector store.
        
        Args:
            documents: List of documents to add
            index_name: Index name (uses default if None)
            
        Returns:
            int: Number of documents added
        """
        if not index_name:
            index_name = Config.PINECONE_INDEX_NAME
        
        response = self.factory.add_documents(documents, index_name)
        if response.success:
            return response.data or 0
        else:
            logger.error(f"Failed to add documents: {response.error}")
            return 0
    
    def similarity_search(self, query: str, k: int = 3, 
                         index_name: Optional[str] = None) -> List[Dict]:
        """
        Search for similar documents.
        
        Args:
            query: Query text
            k: Number of results
            index_name: Index name (uses default if None)
            
        Returns:
            List[Dict]: List of similar documents
        """
        if not index_name:
            index_name = Config.PINECONE_INDEX_NAME
        
        response = self.factory.similarity_search(query, k, index_name)
        if response.success:
            return response.data or []
        else:
            logger.error(f"Search failed: {response.error}")
            return []
    
    def get_stats(self, index_name: Optional[str] = None) -> Dict:
        """
        Get vector store index statistics.
        
        Args:
            index_name: Index name (uses default if None)
            
        Returns:
            Dict: Index statistics
        """
        if not index_name:
            index_name = Config.PINECONE_INDEX_NAME
        
        response = self.factory.get_index_stats(index_name)
        if response.success:
            return response.data or {}
        else:
            logger.error(f"Failed to get stats: {response.error}")
            return {}
    
    def list_documents(self, index_name: Optional[str] = None, 
                      limit: int = 3, 
                      pagination_token: Optional[str] = None) -> Dict:
        """
        List documents from vector store.
        
        Args:
            index_name: Index name (uses default if None)
            limit: Maximum documents to return
            pagination_token: Pagination token
            
        Returns:
            Dict: Documents and pagination info
        """
        if not index_name:
            index_name = Config.PINECONE_INDEX_NAME
        
        response = self.factory.list_documents(index_name, limit, pagination_token)
        if response.success:
            return {
                'documents': response.data or [],
                'next_token': response.metadata.get('next_token') if response.metadata else None
            }
        else:
            logger.error(f"Failed to list documents: {response.error}")
            return {'documents': [], 'next_token': None}
    
    def get_vector_store(self, index_name: Optional[str] = None):
        """
        Get vector store wrapper for direct provider access.
        
        Args:
            index_name: Index name (uses default if None)
            
        Returns:
            SimplifiedVectorStore: Simplified interface to provider
        """
        if not index_name:
            index_name = Config.PINECONE_INDEX_NAME
        
        provider = self.factory.get_current_provider()
        
        class SimplifiedVectorStore:
            """Simplified vector store wrapper for compatibility."""
            
            def __init__(self, factory, index_name):
                self.factory = factory
                self.index_name = index_name
            
            def similarity_search(self, query: str, k: int = 3) -> List:
                """Search for similar documents."""
                response = self.factory.similarity_search(query, k, self.index_name)
                return response.data or [] if response.success else []
            
            def add_documents(self, documents: List) -> int:
                """Add documents to store."""
                response = self.factory.add_documents(documents, self.index_name)
                return response.data or 0 if response.success else 0
        
        return SimplifiedVectorStore(self.factory, index_name)
