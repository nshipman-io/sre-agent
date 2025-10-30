"""Documents API endpoints."""
from typing import Any
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
import structlog

from app.services.document_service import DocumentService
from app.config import settings

logger = structlog.get_logger()
router = APIRouter()


class IndexDocumentRequest(BaseModel):
    """Request model for indexing a document."""

    content: str
    metadata: dict[str, Any]
    doc_id: str | None = None


class IndexDirectoryRequest(BaseModel):
    """Request model for indexing a directory."""

    directory_path: str
    file_extensions: list[str] | None = None


class SearchRequest(BaseModel):
    """Request model for searching documents."""

    query: str
    n_results: int = 5
    filter_metadata: dict[str, Any] | None = None


def get_document_service() -> DocumentService:
    """
    Dependency to get document service instance.

    Returns:
        Configured document service
    """
    return DocumentService(
        openai_api_key=settings.openai_api_key,
        persist_directory=settings.chroma_persist_directory,
        collection_name=settings.chroma_collection_name,
        embedding_model=settings.openai_embedding_model,
    )


@router.post("/index")
async def index_document(
    request: IndexDocumentRequest,
    service: DocumentService = Depends(get_document_service),
) -> dict[str, str]:
    """Index a single document."""
    try:
        doc_id = await service.index_document(
            content=request.content,
            metadata=request.metadata,
            doc_id=request.doc_id,
        )
        return {"doc_id": doc_id, "status": "indexed"}
    except Exception as e:
        logger.error("Failed to index document", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/index-directory")
async def index_directory(
    request: IndexDirectoryRequest,
    service: DocumentService = Depends(get_document_service),
) -> dict[str, Any]:
    """Index all documents in a directory."""
    try:
        count = await service.index_directory(
            directory_path=request.directory_path,
            file_extensions=request.file_extensions,
        )
        return {"indexed_count": count, "status": "completed"}
    except Exception as e:
        logger.error("Failed to index directory", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search")
async def search_documents(
    request: SearchRequest,
    service: DocumentService = Depends(get_document_service),
) -> dict[str, Any]:
    """Search for documents using semantic search."""
    try:
        results = await service.search_documents(
            query=request.query,
            n_results=request.n_results,
            filter_metadata=request.filter_metadata,
        )
        return {"results": results, "count": len(results)}
    except Exception as e:
        logger.error("Failed to search documents", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_stats(
    service: DocumentService = Depends(get_document_service),
) -> dict[str, Any]:
    """Get collection statistics."""
    try:
        return service.get_collection_stats()
    except Exception as e:
        logger.error("Failed to get stats", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{doc_id}")
async def get_document(
    doc_id: str,
    service: DocumentService = Depends(get_document_service),
) -> dict[str, Any]:
    """Get a specific document by ID."""
    try:
        doc = await service.get_document(doc_id)
        if doc is None:
            raise HTTPException(status_code=404, detail="Document not found")
        return doc
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get document", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{doc_id}")
async def delete_document(
    doc_id: str,
    service: DocumentService = Depends(get_document_service),
) -> dict[str, str]:
    """Delete a document by ID."""
    try:
        await service.delete_document(doc_id)
        return {"doc_id": doc_id, "status": "deleted"}
    except Exception as e:
        logger.error("Failed to delete document", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clear")
async def clear_collection(
    service: DocumentService = Depends(get_document_service),
) -> dict[str, str]:
    """Clear all documents from the collection."""
    try:
        await service.clear_collection()
        return {"status": "cleared"}
    except Exception as e:
        logger.error("Failed to clear collection", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
