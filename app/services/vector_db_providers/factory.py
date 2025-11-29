"""
Vector database provider factory.
Manages provider registry, initialization, and selection based on configuration.
"""
import logging
from typing import Dict, List, Optional, Tuple
from app.config import Config
from app.services.vector_db_providers.base import VectorDBProvider

logger = logging.getLogger(__name__)


class VectorDBFactory:
    """Factory for managing vector database providers.
    
    Implements a registry pattern where multiple providers can be registered,
    and the factory selects the configured primary provider with optional fallbacks.
    """
    
    # Provider registry
    _provider_registry: Dict[str, type] = {}
    
    # Singleton instance
    _instance = None
    
    def __init__(self, primary_provider: Optional[str] = None,
                 fallback_providers: Optional[List[str]] = None):
        """
        Initialize vector DB factory.
        
        Args:
            primary_provider: Primary provider to use (defaults to Config.VECTOR_DB_TYPE)
            fallback_providers: List of fallback providers if primary fails
        """
        self.primary_provider_name = primary_provider or Config.VECTOR_DB_TYPE
        self.fallback_provider_names = fallback_providers or Config.VECTOR_DB_FALLBACK_PROVIDERS or []
        
        self.primary_provider = None
        self.fallback_providers = []
        self.current_provider = None
        self.provider_status = {}
        
        self._initialize_providers()
        logger.info(f"VectorDBFactory initialized with primary: {self.primary_provider_name}")
    
    @classmethod
    def register_provider(cls, name: str, provider_class: type) -> None:
        """
        Register a vector database provider.
        
        Args:
            name: Identifier for the provider (e.g., 'pinecone', 'weaviate')
            provider_class: Class implementing VectorDBProvider interface
        """
        if not issubclass(provider_class, VectorDBProvider):
            raise ValueError(f"{provider_class} must inherit from VectorDBProvider")
        
        cls._provider_registry[name.lower()] = provider_class
        logger.info(f"Registered vector DB provider: {name}")
    
    @classmethod
    def get_registered_providers(cls) -> List[str]:
        """Get list of registered provider names."""
        return list(cls._provider_registry.keys())
    
    def _initialize_providers(self) -> None:
        """Initialize primary and fallback providers."""
        all_providers = [self.primary_provider_name] + self.fallback_provider_names
        
        for provider_name in all_providers:
            try:
                provider = self._create_provider(provider_name)
                if provider:
                    if provider_name == self.primary_provider_name:
                        self.primary_provider = provider
                        self.current_provider = provider
                    else:
                        self.fallback_providers.append(provider)
                    
                    self.provider_status[provider_name] = 'initialized'
            except Exception as e:
                logger.error(f"Failed to initialize {provider_name}: {e}")
                self.provider_status[provider_name] = f'error: {e}'
        
        if not self.current_provider:
            logger.error("No vector DB providers successfully initialized")
            raise ValueError("Unable to initialize any vector DB provider")
    
    def _create_provider(self, provider_name: str) -> Optional[VectorDBProvider]:
        """
        Create and initialize a provider instance.
        
        Args:
            provider_name: Name of provider to create
            
        Returns:
            Initialized provider instance or None if creation fails
        """
        provider_name_lower = provider_name.lower()
        
        if provider_name_lower not in self._provider_registry:
            logger.error(f"Provider '{provider_name}' not registered")
            return None
        
        provider_class = self._provider_registry[provider_name_lower]
        
        try:
            provider = provider_class()
            if not provider.initialize():
                logger.error(f"Failed to initialize {provider_name}")
                return None
            
            logger.info(f"Successfully initialized {provider_name} provider")
            return provider
        except Exception as e:
            logger.error(f"Exception creating {provider_name} provider: {e}")
            return None
    
    def get_current_provider(self) -> Optional[VectorDBProvider]:
        """
        Get current active provider.
        
        Returns:
            Current provider instance or None if no provider available
        """
        return self.current_provider
    
    def get_provider_by_name(self, name: str) -> Optional[VectorDBProvider]:
        """
        Get specific provider by name.
        
        Args:
            name: Provider name
            
        Returns:
            Provider instance or None if not found
        """
        if name.lower() == self.primary_provider_name.lower():
            return self.primary_provider
        
        for provider in self.fallback_providers:
            if provider.get_provider_name().lower() == name.lower():
                return provider
        
        return None
    
    def get_provider_status(self) -> Dict:
        """
        Get status of all providers.
        
        Returns:
            Dict with status information for each provider
        """
        status = {
            'primary_provider': self.primary_provider_name,
            'current_provider': self.current_provider.get_provider_name() if self.current_provider else None,
            'fallback_providers': self.fallback_provider_names,
            'providers': {}
        }
        
        # Add primary provider status
        if self.primary_provider:
            status['providers'][self.primary_provider_name] = self.primary_provider.get_provider_status()
        
        # Add fallback provider statuses
        for i, provider in enumerate(self.fallback_providers):
            name = self.fallback_provider_names[i] if i < len(self.fallback_provider_names) else f'fallback_{i}'
            status['providers'][name] = provider.get_provider_status()
        
        return status
    
    def get_or_create_index(self, index_name: str, dimension: Optional[int] = None) -> bool:
        """
        Get or create index in current provider.
        
        Args:
            index_name: Name of index
            dimension: Dimension for embeddings (if creating new)
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.current_provider:
            logger.error("No vector DB provider available")
            return False
        
        return self.current_provider.get_or_create_index(index_name, dimension)
    
    def add_documents(self, documents: List, index_name: str):
        """
        Add documents to current provider.
        
        Args:
            documents: List of documents to add
            index_name: Index name
            
        Returns:
            VectorDBResponse with results
        """
        if not self.current_provider:
            logger.error("No vector DB provider available")
            from app.services.vector_db_providers.base import VectorDBResponse
            return VectorDBResponse(success=False, error="No provider available")
        
        return self.current_provider.add_documents(documents, index_name)
    
    def similarity_search(self, query: str, k: int = 3, index_name: Optional[str] = None):
        """
        Search for similar documents in current provider.
        
        Args:
            query: Query text
            k: Number of results
            index_name: Index name (uses default if None)
            
        Returns:
            VectorDBResponse with search results
        """
        if not self.current_provider:
            logger.error("No vector DB provider available")
            from app.services.vector_db_providers.base import VectorDBResponse
            return VectorDBResponse(success=False, error="No provider available")
        
        return self.current_provider.similarity_search(query, k, index_name)
    
    def get_index_stats(self, index_name: Optional[str] = None):
        """
        Get index statistics from current provider.
        
        Args:
            index_name: Index name (uses default if None)
            
        Returns:
            VectorDBResponse with statistics
        """
        if not self.current_provider:
            logger.error("No vector DB provider available")
            from app.services.vector_db_providers.base import VectorDBResponse
            return VectorDBResponse(success=False, error="No provider available")
        
        return self.current_provider.get_index_stats(index_name)
    
    def list_documents(self, index_name: Optional[str] = None, limit: int = 10,
                      pagination_token: Optional[str] = None):
        """
        List documents in current provider.
        
        Args:
            index_name: Index name (uses default if None)
            limit: Maximum documents to return
            pagination_token: Pagination token
            
        Returns:
            VectorDBResponse with document list
        """
        if not self.current_provider:
            logger.error("No vector DB provider available")
            from app.services.vector_db_providers.base import VectorDBResponse
            return VectorDBResponse(success=False, error="No provider available")
        
        return self.current_provider.list_documents(index_name, limit, pagination_token)
    
    def delete_document(self, document_id: str, index_name: Optional[str] = None):
        """
        Delete document from current provider.
        
        Args:
            document_id: Document ID to delete
            index_name: Index name (uses default if None)
            
        Returns:
            VectorDBResponse with result
        """
        if not self.current_provider:
            logger.error("No vector DB provider available")
            from app.services.vector_db_providers.base import VectorDBResponse
            return VectorDBResponse(success=False, error="No provider available")
        
        return self.current_provider.delete_document(document_id, index_name)


# Register default providers
VectorDBFactory.register_provider('pinecone', __import__(
    'app.services.vector_db_providers.pinecone_provider',
    fromlist=['PineconeProvider']
).PineconeProvider)
