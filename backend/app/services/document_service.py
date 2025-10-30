"""Document indexing and retrieval service using ChromaDB and OpenAI embeddings."""
import os
from pathlib import Path
from typing import Any, Callable
import structlog
import chromadb
from chromadb.config import Settings as ChromaSettings
from openai import OpenAI

logger = structlog.get_logger()


class DocumentService:
    """Service for indexing and searching documentation using vector embeddings."""

    def __init__(
        self,
        openai_api_key: str,
        persist_directory: str,
        collection_name: str,
        embedding_model: str = "text-embedding-3-small",
    ):
        """
        Initialize document service.

        Args:
            openai_api_key: OpenAI API key
            persist_directory: Directory to persist ChromaDB data
            collection_name: Name of the ChromaDB collection
            embedding_model: OpenAI embedding model to use
        """
        self.openai_client = OpenAI(api_key=openai_api_key)
        self.embedding_model = embedding_model
        self.collection_name = collection_name

        # Initialize ChromaDB
        self.chroma_client = chromadb.PersistentClient(
            path=persist_directory,
            settings=ChromaSettings(
                anonymized_telemetry=False,
            ),
        )

        # Get or create collection
        self.collection = self.chroma_client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "SRE runbooks and documentation"},
        )

        logger.info(
            "Initialized document service",
            collection=collection_name,
            persist_directory=persist_directory,
        )

    def _generate_embedding(self, text: str) -> list[float]:
        """
        Generate embedding for text using OpenAI.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        try:
            response = self.openai_client.embeddings.create(
                input=text,
                model=self.embedding_model,
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error("Failed to generate embedding", error=str(e))
            raise

    async def index_document(
        self,
        content: str,
        metadata: dict[str, Any],
        doc_id: str | None = None,
    ) -> str:
        """
        Index a document with its metadata.

        Args:
            content: Document content to index
            metadata: Metadata about the document (e.g., source, title, tags)
            doc_id: Optional custom document ID

        Returns:
            Document ID
        """
        try:
            # Generate embedding
            embedding = self._generate_embedding(content)

            # Generate ID if not provided
            if doc_id is None:
                doc_id = f"doc_{self.collection.count() + 1}"

            # Add to collection
            self.collection.add(
                embeddings=[embedding],
                documents=[content],
                metadatas=[metadata],
                ids=[doc_id],
            )

            logger.info("Indexed document", doc_id=doc_id, metadata=metadata)
            return doc_id

        except Exception as e:
            logger.error("Failed to index document", error=str(e))
            raise

    async def index_directory(
        self,
        directory_path: str,
        file_extensions: list[str] | None = None,
        metadata_fn: Callable | None = None,
    ) -> int:
        """
        Index all documents in a directory.

        Args:
            directory_path: Path to directory containing documents
            file_extensions: List of file extensions to index (e.g., ['.md', '.txt'])
            metadata_fn: Optional function to extract metadata from file path

        Returns:
            Number of documents indexed
        """
        if file_extensions is None:
            file_extensions = [".md", ".txt", ".pdf"]

        directory = Path(directory_path)
        if not directory.exists():
            logger.warning("Directory does not exist", path=directory_path)
            return 0

        indexed_count = 0
        for file_path in directory.rglob("*"):
            if file_path.is_file() and file_path.suffix in file_extensions:
                try:
                    # Read file content
                    content = file_path.read_text(encoding="utf-8")

                    # Generate metadata
                    metadata = {
                        "source": str(file_path),
                        "filename": file_path.name,
                        "extension": file_path.suffix,
                    }

                    # Apply custom metadata function if provided
                    if metadata_fn:
                        custom_metadata = metadata_fn(file_path)
                        metadata.update(custom_metadata)

                    # Index the document
                    doc_id = f"file_{file_path.stem}_{indexed_count}"
                    await self.index_document(content, metadata, doc_id)
                    indexed_count += 1

                except Exception as e:
                    logger.error(
                        "Failed to index file", file=str(file_path), error=str(e)
                    )
                    continue

        logger.info(
            "Indexed directory",
            directory=directory_path,
            indexed_count=indexed_count,
        )
        return indexed_count

    async def search_documents(
        self,
        query: str,
        n_results: int = 5,
        filter_metadata: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Search for relevant documents using semantic search.

        Args:
            query: Search query
            n_results: Number of results to return
            filter_metadata: Optional metadata filters

        Returns:
            List of matching documents with metadata and scores
        """
        try:
            # Generate query embedding
            query_embedding = self._generate_embedding(query)

            # Search collection
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=filter_metadata,
            )

            # Format results
            documents = []
            if results["documents"] and results["documents"][0]:
                for i, doc in enumerate(results["documents"][0]):
                    documents.append(
                        {
                            "content": doc,
                            "metadata": results["metadatas"][0][i],
                            "distance": results["distances"][0][i],
                            "id": results["ids"][0][i],
                        }
                    )

            logger.info(
                "Searched documents",
                query=query,
                results_count=len(documents),
                n_results=n_results,
            )
            return documents

        except Exception as e:
            logger.error("Failed to search documents", error=str(e))
            raise

    async def get_document(self, doc_id: str) -> dict[str, Any] | None:
        """
        Get a specific document by ID.

        Args:
            doc_id: Document ID

        Returns:
            Document data or None if not found
        """
        try:
            result = self.collection.get(ids=[doc_id])

            if result["documents"]:
                return {
                    "content": result["documents"][0],
                    "metadata": result["metadatas"][0],
                    "id": result["ids"][0],
                }

            return None

        except Exception as e:
            logger.error("Failed to get document", doc_id=doc_id, error=str(e))
            raise

    async def delete_document(self, doc_id: str) -> None:
        """
        Delete a document by ID.

        Args:
            doc_id: Document ID
        """
        try:
            self.collection.delete(ids=[doc_id])
            logger.info("Deleted document", doc_id=doc_id)

        except Exception as e:
            logger.error("Failed to delete document", doc_id=doc_id, error=str(e))
            raise

    async def clear_collection(self) -> None:
        """Clear all documents from the collection."""
        try:
            # Delete and recreate collection
            self.chroma_client.delete_collection(name=self.collection_name)
            self.collection = self.chroma_client.create_collection(
                name=self.collection_name,
                metadata={"description": "SRE runbooks and documentation"},
            )
            logger.info("Cleared collection", collection=self.collection_name)

        except Exception as e:
            logger.error("Failed to clear collection", error=str(e))
            raise

    def get_collection_stats(self) -> dict[str, Any]:
        """
        Get statistics about the collection.

        Returns:
            Collection statistics
        """
        try:
            count = self.collection.count()
            return {
                "collection_name": self.collection_name,
                "document_count": count,
            }

        except Exception as e:
            logger.error("Failed to get collection stats", error=str(e))
            raise
