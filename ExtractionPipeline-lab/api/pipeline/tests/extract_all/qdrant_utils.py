
#!/usr/bin/env python3
"""
Qdrant utilities for connectivity checks and collection management.
"""
import asyncio
import logging
from typing import Optional, Dict, Any
import aiohttp
import json
from retry_utils import qdrant_retry


class QdrantUtils:
    """Qdrant utilities for connection checks and collection operations."""
    
    def __init__(self, config):
        """Initialize Qdrant client with configuration."""
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Prepare headers for API requests
        self.headers = {'Content-Type': 'application/json'}
        if config.qdrant_key:
            self.headers['Authorization'] = f'Bearer {config.qdrant_key}'
    
    @qdrant_retry()
    async def check_connection(self) -> bool:
        """Check Qdrant connectivity and service availability."""
        try:
            self.logger.info(f"Checking Qdrant connection to: {self.config.qdrant_url}")
            
            async with aiohttp.ClientSession() as session:
                # Check service health
                health_url = f"{self.config.qdrant_url}/health"
                async with session.get(health_url, headers=self.headers) as response:
                    if response.status == 200:
                        self.logger.info("Qdrant service is healthy")
                    else:
                        raise Exception(f"Qdrant health check failed: {response.status}")
                
                # Check collections endpoint
                collections_url = f"{self.config.qdrant_url}/collections"
                async with session.get(collections_url, headers=self.headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.logger.info(f"Connected to Qdrant. Available collections: {len(data.get('result', {}).get('collections', []))}")
                    else:
                        raise Exception(f"Failed to fetch collections: {response.status}")
                
                return True
                
        except aiohttp.ClientError as e:
            self.logger.error(f"Qdrant connection error: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error checking Qdrant connection: {e}")
            raise
    
    async def check_collection_exists(self, collection_name: Optional[str] = None) -> bool:
        """
        Check if a specific collection exists in Qdrant.
        
        Args:
            collection_name: Name of the collection to check. Defaults to config collection.
        
        Returns:
            True if collection exists, False otherwise
        """
        if collection_name is None:
            collection_name = self.config.qdrant_collection
            
        try:
            self.logger.info(f"Checking if collection '{collection_name}' exists")
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.config.qdrant_url}/collections/{collection_name}"
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        self.logger.info(f"Collection '{collection_name}' exists")
                        return True
                    elif response.status == 404:
                        self.logger.info(f"Collection '{collection_name}' does not exist")
                        return False
                    else:
                        raise Exception(f"Failed to check collection: {response.status}")
                        
        except Exception as e:
            self.logger.error(f"Error checking collection existence: {e}")
            raise
    
    async def get_collection_info(self, collection_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get detailed information about a collection.
        
        Args:
            collection_name: Name of the collection. Defaults to config collection.
        
        Returns:
            Dictionary with collection information
        """
        if collection_name is None:
            collection_name = self.config.qdrant_collection
            
        try:
            self.logger.info(f"Getting info for collection '{collection_name}'")
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.config.qdrant_url}/collections/{collection_name}"
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        result = data.get('result', {})
                        
                        info = {
                            'name': collection_name,
                            'status': result.get('status'),
                            'points_count': result.get('points_count', 0),
                            'segments_count': result.get('segments_count', 0),
                            'config': result.get('config', {}),
                            'payload_schema': result.get('payload_schema', {})
                        }
                        
                        self.logger.info(f"Collection '{collection_name}' has {info['points_count']} points")
                        return info
                    else:
                        raise Exception(f"Failed to get collection info: {response.status}")
                        
        except Exception as e:
            self.logger.error(f"Error getting collection info: {e}")
            raise
    
    async def search_similar_documents(self, query_vector: list, limit: int = 10) -> list:
        """
        Search for similar documents in the collection.
        
        Args:
            query_vector: Vector to search for
            limit: Maximum number of results to return
        
        Returns:
            List of similar documents
        """
        try:
            self.logger.info(f"Searching for similar documents (limit: {limit})")
            
            search_payload = {
                "vector": query_vector,
                "limit": limit,
                "with_payload": True,
                "with_vectors": False
            }
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.config.qdrant_url}/collections/{self.config.qdrant_collection}/points/search"
                async with session.post(url, 
                                      headers=self.headers,
                                      json=search_payload) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        results = data.get('result', [])
                        self.logger.info(f"Found {len(results)} similar documents")
                        return results
                    else:
                        raise Exception(f"Search failed: {response.status}")
                        
        except Exception as e:
            self.logger.error(f"Error searching similar documents: {e}")
            raise
    
    async def count_documents(self, collection_name: Optional[str] = None) -> int:
        """
        Count the number of documents in a collection.
        
        Args:
            collection_name: Name of the collection. Defaults to config collection.
        
        Returns:
            Number of documents in the collection
        """
        if collection_name is None:
            collection_name = self.config.qdrant_collection
            
        try:
            info = await self.get_collection_info(collection_name)
            return info.get('points_count', 0)
        except Exception as e:
            self.logger.error(f"Error counting documents: {e}")
            raise
    
    async def get_collection_stats(self, collection_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get comprehensive statistics for a collection.
        
        Args:
            collection_name: Name of the collection. Defaults to config collection.
        
        Returns:
            Dictionary with collection statistics
        """
        if collection_name is None:
            collection_name = self.config.qdrant_collection
            
        try:
            self.logger.info(f"Getting statistics for collection '{collection_name}'")
            
            info = await self.get_collection_info(collection_name)
            
            stats = {
                'collection_name': collection_name,
                'total_documents': info.get('points_count', 0),
                'segments_count': info.get('segments_count', 0),
                'status': info.get('status'),
                'vector_size': info.get('config', {}).get('params', {}).get('vectors', {}).get('size', 0),
                'distance_metric': info.get('config', {}).get('params', {}).get('vectors', {}).get('distance', 'Unknown'),
                'payload_schema_fields': len(info.get('payload_schema', {}))
            }
            
            self.logger.info(f"Collection stats: {stats['total_documents']} documents, {stats['segments_count']} segments")
            return stats
            
        except Exception as e:
            self.logger.error(f"Error getting collection stats: {e}")
            raise
    
    async def create_collection(self, collection_name: str, vector_size: int = 384, 
                               distance: str = "Cosine") -> bool:
        """
        Create a new collection in Qdrant.
        
        Args:
            collection_name: Name for the new collection
            vector_size: Size of the vectors to store
            distance: Distance metric to use
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info(f"Creating collection '{collection_name}'")
            
            collection_config = {
                "vectors": {
                    "size": vector_size,
                    "distance": distance
                }
            }
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.config.qdrant_url}/collections/{collection_name}"
                async with session.put(url, 
                                     headers=self.headers,
                                     json=collection_config) as response:
                    
                    if response.status == 200:
                        self.logger.info(f"Collection '{collection_name}' created successfully")
                        return True
                    else:
                        response_text = await response.text()
                        self.logger.error(f"Failed to create collection: {response.status} - {response_text}")
                        return False
                        
        except Exception as e:
            self.logger.error(f"Error creating collection: {e}")
            return False
    
    @qdrant_retry()
    async def is_video_extracted(self, code: str, collection_name: Optional[str] = None) -> bool:
        """
        Check if a video with the given code is already extracted in Qdrant.
        
        Args:
            code: Video code to check
            collection_name: Name of the collection. Defaults to config collection.
        
        Returns:
            True if video is already extracted, False otherwise
        """
        if collection_name is None:
            collection_name = self.config.qdrant_collection
            
        try:
            self.logger.debug(f"Checking if video '{code}' is already extracted")
            
            # Search for points with matching video_code
            search_payload = {
                "filter": {
                    "must": [
                        {
                            "key": "platform",
                            "match": {
                                "value": "instagram"
                            }
                        },
                        {
                            "key": "video_code",
                            "match": {
                                "value": code
                            }
                        }
                    ]
                },
                "limit": 1,
                "with_payload": False,
                "with_vectors": False
            }
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.config.qdrant_url}/collections/{collection_name}/points/search"
                async with session.post(url, 
                                      headers=self.headers,
                                      json=search_payload) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        results = data.get('result', [])
                        is_extracted = len(results) > 0
                        
                        self.logger.debug(f"Video '{code}' extraction status: {'already extracted' if is_extracted else 'not extracted'}")
                        return is_extracted
                    elif response.status == 404:
                        # Collection doesn't exist, so video is not extracted
                        self.logger.debug(f"Collection '{collection_name}' does not exist, video '{code}' not extracted")
                        return False
                    else:
                        response_text = await response.text()
                        self.logger.warning(f"Failed to check video extraction status: {response.status} - {response_text}")
                        return False
                        
        except Exception as e:
            self.logger.error(f"Error checking if video '{code}' is extracted: {e}")
            return False
