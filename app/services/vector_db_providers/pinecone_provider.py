"""
Pinecone vector database provider.
Implements VectorDBProvider interface for Pinecone vector DB.
"""
import time
import logging
from typing import List, Dict, Optional, Any
import google.generativeai as genai
from langchain_core.embeddings import Embeddings
from langchain_core.documents import Document
from pinecone import Pinecone, ServerlessSpec
from app.config import Config
from app.services.vector_db_providers.base import VectorDBProvider, VectorDBResponse

logger = logging.getLogger(__name__)


class GoogleGenAIEmbeddings(Embeddings):
    """Custom wrapper for Google Generative AI Embeddings to be compatible with LangChain."""
    
    def __init__(self, api_key, model_name="models/embedding-001"):
        genai.configure(api_key=api_key)
        self.model_name = model_name
        
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of documents."""
        embeddings = []
        for text in texts:
            try:
                result = genai.embed_content(
                    model=self.model_name,
                    content=text,
                    task_type="retrieval_document"
                )
                embeddings.append(result['embedding'])
                time.sleep(1)  # Rate limit
            except Exception as e:
                logger.error(f"Error embedding document: {e}")
                embeddings.append([0.0] * 768)
        return embeddings

    def embed_query(self, text: str) -> List[float]:
        """Embed a query."""
        try:
            result = genai.embed_content(
                model=self.model_name,
                content=text,
                task_type="retrieval_query"
            )
            time.sleep(1)  # Rate limit
            return result['embedding']
        except Exception as e:
            logger.error(f"Error embedding query: {e}")
            return [0.0] * 768


class PineconeProvider(VectorDBProvider):
    """Pinecone vector database provider implementation."""
    
    def __init__(self):
        """Initialize Pinecone provider."""
        self.api_key = Config.PINECONE_API_KEY
        self.index_name = Config.PINECONE_INDEX_NAME
        self.dimension = Config.PINECONE_DIMENSION
        self.metric = Config.PINECONE_METRIC
        self.cloud = Config.PINECONE_CLOUD
        self.region = Config.PINECONE_REGION
        self.embedding_model = Config.EMBEDDING_MODEL
        
        self.pc_client = None
        self.embeddings = None
        self._initialized = False
        
        logger.info("PineconeProvider initialized")
    
    def validate_credentials(self) -> bool:
        """Validate Pinecone credentials."""
        try:
            if not self.api_key:
                logger.error("PINECONE_API_KEY not configured")
                return False
            
            # Try to create client
            pc = Pinecone(api_key=self.api_key)
            logger.info("Pinecone credentials validated successfully")
            return True
        except Exception as e:
            logger.error(f"Pinecone credential validation failed: {e}")
            return False
    
    def is_available(self) -> bool:
        """Check if Pinecone is available."""
        try:
            if not self.pc_client:
                return False
            # Try to list indexes
            self.pc_client.list_indexes()
            logger.debug("Pinecone is available")
            return True
        except Exception as e:
            logger.error(f"Pinecone availability check failed: {e}")
            return False
    
    def initialize(self) -> bool:
        """Initialize Pinecone provider."""
        try:
            if not self.validate_credentials():
                return False
            
            # Initialize embeddings
            if not Config.GOOGLE_API_KEY:
                logger.error("GOOGLE_API_KEY not set for embeddings")
                return False
            
            self.embeddings = GoogleGenAIEmbeddings(
                api_key=Config.GOOGLE_API_KEY,
                model_name=self.embedding_model
            )
            
            # Initialize Pinecone client
            self.pc_client = Pinecone(api_key=self.api_key)
            
            logger.info("PineconeProvider initialized successfully")
            self._initialized = True
            return True
        except Exception as e:
            logger.error(f"PineconeProvider initialization failed: {e}")
            return False
    
    def get_or_create_index(self, index_name: str, dimension: Optional[int] = None) -> bool:
        """Get existing index or create new one."""
        try:
            if not self._initialized or not self.pc_client:
                logger.error("PineconeProvider not initialized")
                return False
            
            existing_indexes = [idx.name for idx in self.pc_client.list_indexes()]
            
            if index_name not in existing_indexes:
                logger.info(f"Creating new Pinecone index: {index_name}")
                if not dimension:
                    dimension = self.dimension
                
                self.pc_client.create_index(
                    name=index_name,
                    dimension=dimension,
                    metric=self.metric,
                    spec=ServerlessSpec(
                        cloud=self.cloud,
                        region=self.region
                    )
                )
                logger.info(f"Index {index_name} created successfully")
            else:
                logger.info(f"Using existing Pinecone index: {index_name}")
            
            return True
        except Exception as e:
            logger.error(f"Error creating/getting index {index_name}: {e}")
            return False
    
    def add_documents(self, documents: List[Dict], index_name: str) -> VectorDBResponse:
        """Add documents to Pinecone."""
        try:
            if not self._initialized or not self.pc_client:
                return VectorDBResponse(
                    success=False,
                    error="PineconeProvider not initialized"
                )
            
            index = self.pc_client.Index(index_name)
            vectors = []
            
            for i, doc in enumerate(documents):
                # Extract content and metadata
                if isinstance(doc, Document):
                    content = doc.page_content
                    metadata = doc.metadata or {}
                else:
                    content = doc.get('page_content', '')
                    metadata = doc.get('metadata', {})
                
                # Generate embedding
                embedding = self.embeddings.embed_documents([content])[0]
                
                # Check for zero vectors
                if all(v == 0.0 for v in embedding):
                    logger.warning(f"Skipping document {i} due to zero-vector embedding")
                    continue
                
                vectors.append({
                    'id': f'doc_{i}_{hash(content)}',
                    'values': embedding,
                    'metadata': {
                        'text': content,
                        **metadata
                    }
                })
            
            # Upsert in batches
            batch_size = 100
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i:i+batch_size]
                index.upsert(vectors=batch)
                logger.debug(f"Upserted batch {i//batch_size + 1} ({len(batch)} vectors)")
            
            logger.info(f"Successfully added {len(vectors)} documents to {index_name}")
            return VectorDBResponse(
                success=True,
                data=len(vectors),
                metadata={'index': index_name, 'vectors_added': len(vectors)}
            )
        except Exception as e:
            logger.error(f"Error adding documents to Pinecone: {e}")
            return VectorDBResponse(success=False, error=str(e))
    
    def similarity_search(self, query: str, k: int = 3, index_name: Optional[str] = None) -> VectorDBResponse:
        """Search for similar documents in Pinecone."""
        try:
            if not self._initialized or not self.pc_client:
                return VectorDBResponse(
                    success=False,
                    error="PineconeProvider not initialized"
                )
            
            if not index_name:
                index_name = self.index_name
            
            index = self.pc_client.Index(index_name)
            
            # Generate query embedding
            query_embedding = self.embeddings.embed_query(query)
            
            # Query Pinecone
            results = index.query(
                vector=query_embedding,
                top_k=k,
                include_metadata=True
            )
            
            # Convert to Document format
            docs = []
            for match in results.get('matches', []):
                metadata = match.get('metadata', {})
                text = metadata.get('text', '')
                docs.append(Document(page_content=text, metadata=metadata))
            
            logger.debug(f"Similarity search found {len(docs)} documents")
            return VectorDBResponse(
                success=True,
                data=docs,
                metadata={'index': index_name, 'query': query, 'results_count': len(docs)}
            )
        except Exception as e:
            logger.error(f"Error in similarity search: {e}")
            return VectorDBResponse(success=False, error=str(e))
    
    def get_index_stats(self, index_name: Optional[str] = None) -> VectorDBResponse:
        """Get Pinecone index statistics."""
        try:
            if not self._initialized or not self.pc_client:
                return VectorDBResponse(
                    success=False,
                    error="PineconeProvider not initialized"
                )
            
            if not index_name:
                index_name = self.index_name
            
            index = self.pc_client.Index(index_name)
            stats = index.describe_index_stats()
            
            logger.debug(f"Retrieved stats for index {index_name}")
            return VectorDBResponse(
                success=True,
                data=stats,
                metadata={'index': index_name}
            )
        except Exception as e:
            logger.error(f"Error getting index stats: {e}")
            return VectorDBResponse(success=False, error=str(e))
    
    def list_documents(self, index_name: Optional[str] = None, limit: int = 10,
                      pagination_token: Optional[str] = None) -> VectorDBResponse:
        """List documents in Pinecone index."""
        try:
            if not self._initialized or not self.pc_client:
                return VectorDBResponse(
                    success=False,
                    error="PineconeProvider not initialized"
                )
            
            if not index_name:
                index_name = self.index_name
            
            index = self.pc_client.Index(index_name)
            
            # Build list arguments
            list_args = {'limit': limit}
            if pagination_token:
                list_args['pagination_token'] = pagination_token
            
            results = index.list(**list_args)
            
            # Extract IDs and fetch documents
            ids = []
            next_token = None
            
            try:
                for batch in results:
                    ids.extend(batch)
                    break
            except TypeError:
                if hasattr(results, 'vectors'):
                    ids = [v.id for v in results.vectors]
                if hasattr(results, 'pagination'):
                    next_token = results.pagination.next
            
            # Fetch document metadata
            documents = []
            if ids:
                fetch_response = index.fetch(ids)
                for vector_id, vector_data in fetch_response.vectors.items():
                    metadata = vector_data.metadata or {}
                    text = metadata.get('text', '')
                    documents.append({
                        'id': vector_id,
                        'text': text,
                        'metadata': metadata
                    })
            
            logger.debug(f"Listed {len(documents)} documents from {index_name}")
            return VectorDBResponse(
                success=True,
                data=documents,
                metadata={
                    'index': index_name,
                    'count': len(documents),
                    'next_token': next_token
                }
            )
        except Exception as e:
            logger.error(f"Error listing documents: {e}")
            return VectorDBResponse(success=False, error=str(e))
    
    def delete_document(self, document_id: str, index_name: Optional[str] = None) -> VectorDBResponse:
        """Delete a document from Pinecone."""
        try:
            if not self._initialized or not self.pc_client:
                return VectorDBResponse(
                    success=False,
                    error="PineconeProvider not initialized"
                )
            
            if not index_name:
                index_name = self.index_name
            
            index = self.pc_client.Index(index_name)
            index.delete(ids=[document_id])
            
            logger.info(f"Deleted document {document_id} from {index_name}")
            return VectorDBResponse(
                success=True,
                metadata={'index': index_name, 'document_id': document_id}
            )
        except Exception as e:
            logger.error(f"Error deleting document: {e}")
            return VectorDBResponse(success=False, error=str(e))
    
    def get_provider_name(self) -> str:
        """Get provider name."""
        return "pinecone"
    
    def get_provider_status(self) -> Dict[str, Any]:
        """Get Pinecone provider status."""
        try:
            if not self._initialized or not self.pc_client:
                return {
                    'name': 'pinecone',
                    'status': 'not_initialized',
                    'available': False
                }
            
            indexes = [idx.name for idx in self.pc_client.list_indexes()]
            
            return {
                'name': 'pinecone',
                'status': 'initialized',
                'available': True,
                'default_index': self.index_name,
                'indexes': indexes,
                'dimension': self.dimension,
                'metric': self.metric,
                'region': self.region
            }
        except Exception as e:
            logger.error(f"Error getting provider status: {e}")
            return {
                'name': 'pinecone',
                'status': 'error',
                'available': False,
                'error': str(e)
            }
