"""
Service for generating embeddings using Azure OpenAI.
"""

import os
import logging
from typing import List, Optional
from openai import AzureOpenAI
import yaml

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Service for generating text embeddings using Azure OpenAI.
    """
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize the embedding service."""
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        
        if not endpoint or not api_key:
            raise ValueError("AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY must be set")
        
        self.client = AzureOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version=self.config['azure_openai']['api_version']
        )
        
        self.embedding_deployment = self.config['models']['embedding']['deployment_name']
        self.embedding_dimensions = self.config['models']['embedding'].get('dimensions', 3072)
        
        logger.info(f"EmbeddingService initialized with model: {self.embedding_deployment}")
    
    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
        
        Returns:
            List of floats representing the embedding, or None if failed
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for embedding")
            return None
        
        try:
            # Truncate if too long (max ~8000 tokens for embedding models)
            max_chars = 30000
            if len(text) > max_chars:
                text = text[:max_chars]
                logger.warning(f"Text truncated to {max_chars} characters")
            
            response = self.client.embeddings.create(
                model=self.embedding_deployment,
                input=text
            )
            
            embedding = response.data[0].embedding
            logger.info(f"Generated embedding with {len(embedding)} dimensions")
            
            return embedding
        
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return None
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
        
        Returns:
            List of embeddings (some may be None if failed)
        """
        embeddings = []
        
        for i, text in enumerate(texts):
            logger.info(f"Generating embedding {i+1}/{len(texts)}")
            embedding = self.generate_embedding(text)
            embeddings.append(embedding)
        
        return embeddings
    
    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """
        Split text into overlapping chunks for embedding.
        
        Args:
            text: Text to chunk
            chunk_size: Maximum characters per chunk
            overlap: Number of overlapping characters between chunks
        
        Returns:
            List of text chunks
        """
        if not text or len(text) <= chunk_size:
            return [text] if text else []
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # Try to break at a sentence or word boundary
            if end < len(text):
                # Look for sentence boundary
                for sep in ['. ', '.\n', '! ', '? ', '\n\n']:
                    last_sep = text[start:end].rfind(sep)
                    if last_sep != -1 and last_sep > chunk_size // 2:
                        end = start + last_sep + len(sep)
                        break
                else:
                    # Look for word boundary
                    last_space = text[start:end].rfind(' ')
                    if last_space != -1 and last_space > chunk_size // 2:
                        end = start + last_space + 1
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - overlap
            if start < 0:
                start = 0
        
        logger.info(f"Split text into {len(chunks)} chunks")
        return chunks
    
    def compute_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Compute cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding
            embedding2: Second embedding
        
        Returns:
            Cosine similarity score (0 to 1)
        """
        if not embedding1 or not embedding2:
            return 0.0
        
        if len(embedding1) != len(embedding2):
            logger.error("Embedding dimensions don't match")
            return 0.0
        
        # Compute dot product
        dot_product = sum(a * b for a, b in zip(embedding1, embedding2))
        
        # Compute magnitudes
        magnitude1 = sum(a * a for a in embedding1) ** 0.5
        magnitude2 = sum(b * b for b in embedding2) ** 0.5
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        # Cosine similarity
        similarity = dot_product / (magnitude1 * magnitude2)
        
        # Normalize to 0-1 range (cosine similarity is -1 to 1)
        normalized = (similarity + 1) / 2
        
        return normalized