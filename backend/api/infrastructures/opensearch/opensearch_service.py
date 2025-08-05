"""AWS OpenSearch service for document search and indexing."""

import json
import os
from typing import Any, Dict, List, Optional
from uuid import UUID

from opensearchpy import OpenSearch, RequestsHttpConnection
from opensearchpy.exceptions import NotFoundError, RequestError


class OpenSearchService:
    """AWS OpenSearch service for automotive diagnostic documents."""
    
    def __init__(self) -> None:
        """Initialize OpenSearch client."""
        self.endpoint = os.environ.get("AWS_OPENSEARCH_ENDPOINT")
        self.region = os.environ.get("AWS_REGION", "us-east-1")
        
        if not self.endpoint:
            # For local development, use localhost
            self.client = OpenSearch(
                hosts=[{"host": "localhost", "port": 9200}],
                http_compress=True,
                use_ssl=False,
                verify_certs=False,
                ssl_assert_hostname=False,
                ssl_show_warn=False,
                connection_class=RequestsHttpConnection,
            )
        else:
            # For AWS managed OpenSearch
            from opensearchpy import AWSV4SignerAuth
            import boto3
            
            credentials = boto3.Session().get_credentials()
            auth = AWSV4SignerAuth(credentials, self.region)
            
            self.client = OpenSearch(
                hosts=[{"host": self.endpoint, "port": 443}],
                http_auth=auth,
                use_ssl=True,
                verify_certs=True,
                connection_class=RequestsHttpConnection,
            )
    
    def create_automotive_index(self, index_name: str) -> None:
        """Create index for automotive diagnostic documents."""
        index_mapping = {
            "mappings": {
                "properties": {
                    "id": {"type": "keyword"},
                    "article_id": {"type": "keyword"},
                    "create_time": {"type": "date"},
                    "category_id": {"type": "keyword"},
                    "text": {
                        "type": "text",
                        "analyzer": "japanese",
                        "fields": {
                            "keyword": {"type": "keyword"}
                        }
                    },
                    "summary": {
                        "type": "text",
                        "analyzer": "japanese"
                    },
                    "article_length": {"type": "integer"},
                    "sentence_scores": {"type": "nested"},
                    "obd_codes": {
                        "type": "nested",
                        "properties": {
                            "code": {"type": "keyword"},
                            "description": {"type": "text", "analyzer": "japanese"}
                        }
                    },
                    "vehicle_info": {
                        "type": "object",
                        "properties": {
                            "make": {"type": "keyword"},
                            "model": {"type": "keyword"},
                            "year": {"type": "integer"}
                        }
                    },
                    "content_vector": {
                        "type": "knn_vector",
                        "dimension": 1536,
                        "method": {
                            "name": "hnsw",
                            "space_type": "cosinesimil",
                            "engine": "nmslib"
                        }
                    }
                }
            },
            "settings": {
                "analysis": {
                    "analyzer": {
                        "japanese": {
                            "type": "kuromoji",
                            "mode": "search"
                        }
                    }
                },
                "index.knn": True
            }
        }
        
        try:
            if not self.client.indices.exists(index=index_name):
                self.client.indices.create(index=index_name, body=index_mapping)
        except RequestError as e:
            raise Exception(f"Failed to create index {index_name}: {e}")
    
    def index_document(self, index_name: str, doc_id: str, document: Dict[str, Any]) -> bool:
        """Index a single document."""
        try:
            response = self.client.index(
                index=index_name,
                id=doc_id,
                body=document,
                refresh=True
            )
            return response["result"] in ["created", "updated"]
        except RequestError as e:
            raise Exception(f"Failed to index document {doc_id}: {e}")
    
    def bulk_index_documents(self, index_name: str, documents: List[Dict[str, Any]]) -> List[str]:
        """Bulk index multiple documents."""
        from opensearchpy.helpers import bulk
        
        actions = []
        for doc in documents:
            action = {
                "_index": index_name,
                "_id": doc.get("id", doc.get("article_id")),
                "_source": doc
            }
            actions.append(action)
        
        try:
            success_count, failed_items = bulk(self.client, actions)
            return [item["_id"] for item in actions[:success_count]]
        except Exception as e:
            raise Exception(f"Bulk indexing failed: {e}")
    
    def search_documents(
        self,
        index_name: str,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        vector: Optional[List[float]] = None,
        size: int = 10,
        from_: int = 0
    ) -> Dict[str, Any]:
        """Search documents with text and/or vector search."""
        search_body = {
            "size": size,
            "from": from_,
            "query": {
                "bool": {
                    "must": [],
                    "filter": []
                }
            }
        }
        
        # Add text search
        if query:
            search_body["query"]["bool"]["must"].append({
                "multi_match": {
                    "query": query,
                    "fields": ["text^2", "summary", "obd_codes.description"],
                    "type": "best_fields",
                    "analyzer": "japanese"
                }
            })
        
        # Add filters
        if filters:
            for field, value in filters.items():
                search_body["query"]["bool"]["filter"].append({
                    "term": {field: value}
                })
        
        # Add vector search
        if vector:
            search_body["knn"] = {
                "content_vector": {
                    "vector": vector,
                    "k": size
                }
            }
        
        try:
            response = self.client.search(index=index_name, body=search_body)
            return response
        except NotFoundError:
            raise Exception(f"Index {index_name} not found")
        except RequestError as e:
            raise Exception(f"Search failed: {e}")
    
    def search_obd_codes(self, index_name: str, obd_code: str) -> Dict[str, Any]:
        """Search for specific OBD diagnostic codes."""
        search_body = {
            "query": {
                "nested": {
                    "path": "obd_codes",
                    "query": {
                        "term": {"obd_codes.code": obd_code}
                    }
                }
            },
            "highlight": {
                "fields": {
                    "obd_codes.description": {}
                }
            }
        }
        
        try:
            return self.client.search(index=index_name, body=search_body)
        except Exception as e:
            raise Exception(f"OBD code search failed: {e}")
    
    def delete_document(self, index_name: str, doc_id: str) -> bool:
        """Delete a document by ID."""
        try:
            response = self.client.delete(index=index_name, id=doc_id)
            return response["result"] == "deleted"
        except NotFoundError:
            return False
        except RequestError as e:
            raise Exception(f"Failed to delete document {doc_id}: {e}")
    
    def get_index_stats(self, index_name: str) -> Dict[str, Any]:
        """Get index statistics."""
        try:
            return self.client.indices.stats(index=index_name)
        except NotFoundError:
            raise Exception(f"Index {index_name} not found")
    
    def delete_index(self, index_name: str) -> bool:
        """Delete an index."""
        try:
            response = self.client.indices.delete(index=index_name)
            return response["acknowledged"]
        except NotFoundError:
            return False
        except RequestError as e:
            raise Exception(f"Failed to delete index {index_name}: {e}")