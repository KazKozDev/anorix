"""
Smart memory (Vector DB) implementation.
Stores conversation texts as numerical vectors for semantic search.
"""

import logging
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path

try:
    import chromadb
    from chromadb.config import Settings
    from sentence_transformers import SentenceTransformer
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    chromadb = None
    SentenceTransformer = None


class SmartMemory:
    """
    Smart memory for semantic search using vector embeddings.
    Stores conversation texts as vectors in ChromaDB for similarity-based retrieval.
    """

    def __init__(self,
                 db_path: str = "data/vector_db",
                 collection_name: str = "conversations",
                 embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """
        Initialize smart memory.

        Args:
            db_path: Path to vector database directory
            collection_name: Name of the collection
            embedding_model: Name of the embedding model
        """
        if not CHROMADB_AVAILABLE:
            raise ImportError(
                "ChromaDB and sentence-transformers are required for smart memory. "
                "Install them with: pip install chromadb sentence-transformers"
            )

        self.db_path = Path(db_path)
        self.db_path.mkdir(parents=True, exist_ok=True)
        self.collection_name = collection_name
        self.embedding_model_name = embedding_model
        self.logger = logging.getLogger(__name__)

        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=str(self.db_path),
            settings=Settings(anonymized_telemetry=False)
        )

        # Initialize embedding model
        self.embedding_model = SentenceTransformer(embedding_model)

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "Conversation memories for semantic search"}
        )

    def _generate_id(self, content: str, timestamp: str) -> str:
        """
        Generate unique ID for content.

        Args:
            content: Text content
            timestamp: Timestamp string

        Returns:
            Unique ID
        """
        content_hash = hashlib.md5(f"{content}_{timestamp}".encode()).hexdigest()
        return f"mem_{content_hash}"

    def _create_embedding(self, text: str) -> List[float]:
        """
        Create embedding for text.

        Args:
            text: Input text

        Returns:
            Embedding vector
        """
        embedding = self.embedding_model.encode(text, convert_to_tensor=False)
        return embedding.tolist()

    def add_conversation(self,
                        role: str,
                        content: str,
                        session_id: str,
                        metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Add conversation to smart memory.

        Args:
            role: Message role (user, assistant, system)
            content: Message content
            session_id: Session identifier
            metadata: Additional metadata

        Returns:
            Document ID
        """
        timestamp = datetime.now().isoformat()
        doc_id = self._generate_id(content, timestamp)

        # Create embedding
        embedding = self._create_embedding(content)

        # Prepare metadata
        doc_metadata = {
            "role": role,
            "session_id": session_id,
            "timestamp": timestamp,
            "content_length": len(content),
            **(metadata or {})
        }

        # Add to collection
        self.collection.add(
            ids=[doc_id],
            embeddings=[embedding],
            documents=[content],
            metadatas=[doc_metadata]
        )

        self.logger.debug(f"Added conversation to smart memory: {role} - {len(content)} chars")
        return doc_id

    def search_similar(self,
                      query: str,
                      n_results: int = 5,
                      where: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Search for similar conversations.

        Args:
            query: Search query
            n_results: Number of results to return
            where: Metadata filters

        Returns:
            List of similar conversations
        """
        if not query.strip():
            return []

        # Create query embedding
        query_embedding = self._create_embedding(query)

        # Search in collection
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where,
            include=["documents", "metadatas", "distances"]
        )

        # Format results
        similar_conversations = []
        if results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                similar_conversations.append({
                    "content": doc,
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i],
                    "similarity": 1 - results["distances"][0][i]  # Convert distance to similarity
                })

        return similar_conversations

    def search_by_session(self,
                         session_id: str,
                         query: Optional[str] = None,
                         n_results: int = 10) -> List[Dict[str, Any]]:
        """
        Search conversations within a specific session.

        Args:
            session_id: Session identifier
            query: Optional semantic query
            n_results: Number of results to return

        Returns:
            List of conversations from the session
        """
        where_filter = {"session_id": session_id}

        if query and query.strip():
            return self.search_similar(
                query=query,
                n_results=n_results,
                where=where_filter
            )
        else:
            # Get all conversations from session
            results = self.collection.get(
                where=where_filter,
                include=["documents", "metadatas"]
            )

            conversations = []
            if results["documents"]:
                for i, doc in enumerate(results["documents"]):
                    conversations.append({
                        "content": doc,
                        "metadata": results["metadatas"][i],
                        "distance": 0.0,
                        "similarity": 1.0
                    })

            # Sort by timestamp
            conversations.sort(
                key=lambda x: x["metadata"].get("timestamp", ""),
                reverse=True
            )

            return conversations[:n_results]

    def search_by_role(self,
                      role: str,
                      query: Optional[str] = None,
                      n_results: int = 10) -> List[Dict[str, Any]]:
        """
        Search conversations by role.

        Args:
            role: Message role (user, assistant, system)
            query: Optional semantic query
            n_results: Number of results to return

        Returns:
            List of conversations from the role
        """
        where_filter = {"role": role}

        if query and query.strip():
            return self.search_similar(
                query=query,
                n_results=n_results,
                where=where_filter
            )
        else:
            # Get all conversations from role
            results = self.collection.get(
                where=where_filter,
                include=["documents", "metadatas"]
            )

            conversations = []
            if results["documents"]:
                for i, doc in enumerate(results["documents"]):
                    conversations.append({
                        "content": doc,
                        "metadata": results["metadatas"][i],
                        "distance": 0.0,
                        "similarity": 1.0
                    })

            # Sort by timestamp
            conversations.sort(
                key=lambda x: x["metadata"].get("timestamp", ""),
                reverse=True
            )

            return conversations[:n_results]

    def get_conversation_themes(self, n_clusters: int = 5) -> List[Dict[str, Any]]:
        """
        Get conversation themes using clustering.

        Args:
            n_clusters: Number of theme clusters

        Returns:
            List of conversation themes
        """
        # Get all documents
        results = self.collection.get(include=["documents", "metadatas"])

        if not results["documents"] or len(results["documents"]) < n_clusters:
            return []

        try:
            from sklearn.cluster import KMeans
            import numpy as np

            # Get embeddings for all documents
            embeddings = []
            for doc in results["documents"]:
                embedding = self._create_embedding(doc)
                embeddings.append(embedding)

            embeddings_array = np.array(embeddings)

            # Perform clustering
            kmeans = KMeans(n_clusters=n_clusters, random_state=42)
            cluster_labels = kmeans.fit_predict(embeddings_array)

            # Group documents by cluster
            themes = []
            for cluster_id in range(n_clusters):
                cluster_docs = []
                cluster_metadata = []

                for i, label in enumerate(cluster_labels):
                    if label == cluster_id:
                        cluster_docs.append(results["documents"][i])
                        cluster_metadata.append(results["metadatas"][i])

                if cluster_docs:
                    # Find most representative document (closest to centroid)
                    cluster_center = kmeans.cluster_centers_[cluster_id]
                    distances = []
                    for i, label in enumerate(cluster_labels):
                        if label == cluster_id:
                            distance = np.linalg.norm(embeddings_array[i] - cluster_center)
                            distances.append((distance, i))

                    distances.sort()
                    representative_idx = distances[0][1]

                    themes.append({
                        "theme_id": cluster_id,
                        "representative_text": results["documents"][representative_idx],
                        "representative_metadata": results["metadatas"][representative_idx],
                        "document_count": len(cluster_docs),
                        "documents": cluster_docs[:3]  # Show first 3 docs as examples
                    })

            return themes

        except ImportError:
            self.logger.warning("scikit-learn not available for clustering")
            return []

    def delete_session(self, session_id: str) -> int:
        """
        Delete all conversations from a session.

        Args:
            session_id: Session identifier

        Returns:
            Number of deleted documents
        """
        # Get documents to delete
        results = self.collection.get(
            where={"session_id": session_id},
            include=["metadatas"]
        )

        if not results["ids"]:
            return 0

        # Delete documents
        self.collection.delete(ids=results["ids"])
        deleted_count = len(results["ids"])

        self.logger.debug(f"Deleted {deleted_count} documents from session {session_id}")
        return deleted_count

    def clear_all(self) -> None:
        """Clear all memories from smart memory."""
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.create_collection(
            name=self.collection_name,
            metadata={"description": "Conversation memories for semantic search"}
        )
        self.logger.debug("Cleared all smart memory")

    def get_memory_stats(self) -> Dict[str, Any]:
        """
        Get memory statistics.

        Returns:
            Memory statistics
        """
        count = self.collection.count()

        # Calculate storage size estimate
        db_size = 0
        if self.db_path.exists():
            for file_path in self.db_path.rglob("*"):
                if file_path.is_file():
                    db_size += file_path.stat().st_size

        return {
            "total_documents": count,
            "collection_name": self.collection_name,
            "embedding_model": self.embedding_model_name,
            "storage_size_bytes": db_size,
            "storage_size_mb": round(db_size / (1024 * 1024), 2),
            "embedding_dimension": len(self._create_embedding("test")) if count > 0 else 0
        }