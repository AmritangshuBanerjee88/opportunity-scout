"""
Service for Azure AI Search operations.
Handles indexing and searching of profiles and opportunities.
"""

import os
import json
import logging
import uuid
from typing import List, Dict, Any, Optional
import requests
import yaml

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AzureSearchService:
    """
    Service for Azure AI Search operations.
    """
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize the search service."""
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
        self.api_key = os.getenv("AZURE_SEARCH_API_KEY")
        
        if not self.endpoint or not self.api_key:
            raise ValueError("AZURE_SEARCH_ENDPOINT and AZURE_SEARCH_API_KEY must be set")
        
        self.api_version = "2023-11-01"
        self.index_name = self.config.get('azure_search', {}).get('index_name', 'proposal-architect-index')
        self.embedding_dimensions = self.config['models']['embedding'].get('dimensions', 3072)
        
        logger.info(f"AzureSearchService initialized with index: {self.index_name}")
    
    def _make_request(self, method: str, url: str, data: Optional[Dict] = None) -> Dict:
        """Make a request to Azure Search API."""
        headers = {
            "api-key": self.api_key,
            "Content-Type": "application/json"
        }
        
        try:
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=30)
            elif method == "POST":
                response = requests.post(url, headers=headers, json=data, timeout=30)
            elif method == "PUT":
                response = requests.put(url, headers=headers, json=data, timeout=30)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers, timeout=30)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            if response.status_code in [200, 201, 204]:
                if response.text:
                    return response.json()
                return {}
            else:
                logger.error(f"Request failed: {response.status_code} - {response.text}")
                return {"error": response.text}
        
        except Exception as e:
            logger.error(f"Request error: {e}")
            return {"error": str(e)}
    
    def create_index(self) -> bool:
        """Create the search index if it doesn't exist."""
        
        index_schema = {
            "name": self.index_name,
            "fields": [
                {"name": "id", "type": "Edm.String", "key": True, "searchable": False},
                {"name": "session_id", "type": "Edm.String", "searchable": False, "filterable": True},
                {"name": "document_type", "type": "Edm.String", "searchable": False, "filterable": True},
                {"name": "content", "type": "Edm.String", "searchable": True, "analyzer": "standard.lucene"},
                {"name": "title", "type": "Edm.String", "searchable": True, "analyzer": "standard.lucene"},
                {"name": "metadata", "type": "Edm.String", "searchable": False},
                {
                    "name": "content_vector",
                    "type": "Collection(Edm.Single)",
                    "searchable": True,
                    "dimensions": self.embedding_dimensions,
                    "vectorSearchProfile": "vector-profile"
                }
            ],
            "vectorSearch": {
                "algorithms": [
                    {
                        "name": "hnsw-algorithm",
                        "kind": "hnsw",
                        "hnswParameters": {
                            "m": 4,
                            "efConstruction": 400,
                            "efSearch": 500,
                            "metric": "cosine"
                        }
                    }
                ],
                "profiles": [
                    {
                        "name": "vector-profile",
                        "algorithm": "hnsw-algorithm"
                    }
                ]
            }
        }
        
        url = f"{self.endpoint}/indexes/{self.index_name}?api-version={self.api_version}"
        
        result = self._make_request("PUT", url, index_schema)
        
        if "error" not in result:
            logger.info(f"Index '{self.index_name}' created/updated successfully")
            return True
        else:
            logger.error(f"Failed to create index: {result.get('error')}")
            return False
    
    def delete_index(self) -> bool:
        """Delete the search index."""
        url = f"{self.endpoint}/indexes/{self.index_name}?api-version={self.api_version}"
        result = self._make_request("DELETE", url)
        
        if "error" not in result:
            logger.info(f"Index '{self.index_name}' deleted successfully")
            return True
        return False
    
    def index_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """
        Index documents into Azure Search.
        
        Args:
            documents: List of documents to index
        
        Returns:
            True if successful
        """
        if not documents:
            logger.warning("No documents to index")
            return True
        
        # Prepare documents for indexing
        actions = []
        for doc in documents:
            action = {
                "@search.action": "upload",
                "id": doc.get("id", str(uuid.uuid4())),
                "session_id": doc.get("session_id", ""),
                "document_type": doc.get("document_type", "unknown"),
                "content": doc.get("content", ""),
                "title": doc.get("title", ""),
                "metadata": json.dumps(doc.get("metadata", {}))
            }
            
            if doc.get("embedding"):
                action["content_vector"] = doc["embedding"]
            
            actions.append(action)
        
        url = f"{self.endpoint}/indexes/{self.index_name}/docs/index?api-version={self.api_version}"
        
        result = self._make_request("POST", url, {"value": actions})
        
        if "error" not in result:
            logger.info(f"Indexed {len(documents)} documents successfully")
            return True
        else:
            logger.error(f"Failed to index documents: {result.get('error')}")
            return False
    
    def search_by_vector(
        self,
        embedding: List[float],
        session_id: str,
        document_type: Optional[str] = None,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search documents by vector similarity.
        
        Args:
            embedding: Query embedding
            session_id: Session ID to filter by
            document_type: Optional document type filter
            top_k: Number of results to return
        
        Returns:
            List of matching documents
        """
        filter_parts = [f"session_id eq '{session_id}'"]
        if document_type:
            filter_parts.append(f"document_type eq '{document_type}'")
        
        filter_str = " and ".join(filter_parts)
        
        search_body = {
            "vectorQueries": [
                {
                    "kind": "vector",
                    "vector": embedding,
                    "fields": "content_vector",
                    "k": top_k
                }
            ],
            "filter": filter_str,
            "select": "id, session_id, document_type, content, title, metadata",
            "top": top_k
        }
        
        url = f"{self.endpoint}/indexes/{self.index_name}/docs/search?api-version={self.api_version}"
        
        result = self._make_request("POST", url, search_body)
        
        if "error" in result:
            logger.error(f"Search failed: {result.get('error')}")
            return []
        
        documents = []
        for hit in result.get("value", []):
            doc = {
                "id": hit.get("id"),
                "session_id": hit.get("session_id"),
                "document_type": hit.get("document_type"),
                "content": hit.get("content"),
                "title": hit.get("title"),
                "score": hit.get("@search.score", 0)
            }
            
            if hit.get("metadata"):
                try:
                    doc["metadata"] = json.loads(hit["metadata"])
                except:
                    doc["metadata"] = {}
            
            documents.append(doc)
        
        logger.info(f"Found {len(documents)} matching documents")
        return documents
    
    def search_by_text(
        self,
        query: str,
        session_id: str,
        document_type: Optional[str] = None,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search documents by text query.
        
        Args:
            query: Text query
            session_id: Session ID to filter by
            document_type: Optional document type filter
            top_k: Number of results to return
        
        Returns:
            List of matching documents
        """
        filter_parts = [f"session_id eq '{session_id}'"]
        if document_type:
            filter_parts.append(f"document_type eq '{document_type}'")
        
        filter_str = " and ".join(filter_parts)
        
        search_body = {
            "search": query,
            "filter": filter_str,
            "select": "id, session_id, document_type, content, title, metadata",
            "top": top_k
        }
        
        url = f"{self.endpoint}/indexes/{self.index_name}/docs/search?api-version={self.api_version}"
        
        result = self._make_request("POST", url, search_body)
        
        if "error" in result:
            logger.error(f"Search failed: {result.get('error')}")
            return []
        
        documents = []
        for hit in result.get("value", []):
            doc = {
                "id": hit.get("id"),
                "session_id": hit.get("session_id"),
                "document_type": hit.get("document_type"),
                "content": hit.get("content"),
                "title": hit.get("title"),
                "score": hit.get("@search.score", 0)
            }
            
            if hit.get("metadata"):
                try:
                    doc["metadata"] = json.loads(hit["metadata"])
                except:
                    doc["metadata"] = {}
            
            documents.append(doc)
        
        return documents
    
    def delete_session_documents(self, session_id: str) -> bool:
        """Delete all documents for a session."""
        
        # First, search for all documents in the session
        search_body = {
            "search": "*",
            "filter": f"session_id eq '{session_id}'",
            "select": "id",
            "top": 1000
        }
        
        url = f"{self.endpoint}/indexes/{self.index_name}/docs/search?api-version={self.api_version}"
        result = self._make_request("POST", url, search_body)
        
        if "error" in result:
            return False
        
        doc_ids = [hit["id"] for hit in result.get("value", [])]
        
        if not doc_ids:
            return True
        
        # Delete documents
        actions = [{"@search.action": "delete", "id": doc_id} for doc_id in doc_ids]
        
        url = f"{self.endpoint}/indexes/{self.index_name}/docs/index?api-version={self.api_version}"
        result = self._make_request("POST", url, {"value": actions})
        
        if "error" not in result:
            logger.info(f"Deleted {len(doc_ids)} documents for session {session_id}")
            return True
        
        return False