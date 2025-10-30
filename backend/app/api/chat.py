"""Chat API endpoints."""
from typing import Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import structlog

from app.services.ai_agent import SREAgent
from app.services.k8s_client import K8sClient
from app.services.document_service import DocumentService
from app.config import settings

logger = structlog.get_logger()
router = APIRouter()


class ChatMessage(BaseModel):
    """Chat message model."""

    message: str
    namespace: str = "default"
    conversation_history: list[dict[str, str]] = []


class ChatResponse(BaseModel):
    """Chat response model."""

    response: str
    tool_calls: list[dict[str, Any]]
    model: str


def get_sre_agent() -> SREAgent:
    """
    Dependency to get SRE agent instance.

    Returns:
        Configured SRE agent
    """
    k8s_client = K8sClient(config_path=settings.k8s_config_path)
    document_service = DocumentService(
        openai_api_key=settings.openai_api_key,
        persist_directory=settings.chroma_persist_directory,
        collection_name=settings.chroma_collection_name,
        embedding_model=settings.openai_embedding_model,
    )
    agent = SREAgent(
        openai_api_key=settings.openai_api_key,
        k8s_client=k8s_client,
        document_service=document_service,
        model=settings.openai_model,
    )
    return agent


@router.post("/message", response_model=ChatResponse)
async def send_message(
    chat_message: ChatMessage,
    agent: SREAgent = Depends(get_sre_agent),
) -> ChatResponse:
    """
    Send a message to the SRE agent.

    Args:
        chat_message: User message and context
        agent: SRE agent instance

    Returns:
        Agent response
    """
    try:
        logger.info(
            "Processing chat message",
            message=chat_message.message,
            namespace=chat_message.namespace,
        )

        response = await agent.chat(
            user_message=chat_message.message,
            conversation_history=chat_message.conversation_history,
            namespace=chat_message.namespace,
        )

        return ChatResponse(**response)

    except Exception as e:
        logger.error("Failed to process message", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze-pods")
async def analyze_pods(
    namespace: str = "default",
    label_selector: str | None = None,
    agent: SREAgent = Depends(get_sre_agent),
) -> dict[str, Any]:
    """
    Proactively analyze pods for issues.

    Args:
        namespace: Kubernetes namespace
        label_selector: Label selector for filtering pods
        agent: SRE agent instance

    Returns:
        Analysis results
    """
    try:
        logger.info(
            "Analyzing pods",
            namespace=namespace,
            label_selector=label_selector,
        )

        analysis = await agent.analyze_pod_issues(namespace, label_selector)
        return analysis

    except Exception as e:
        logger.error("Failed to analyze pods", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
