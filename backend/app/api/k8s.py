"""Kubernetes API endpoints."""
from typing import Any
from fastapi import APIRouter, HTTPException, Depends, Query
import structlog

from app.services.k8s_client import K8sClient
from app.config import settings

logger = structlog.get_logger()
router = APIRouter()


def get_k8s_client() -> K8sClient:
    """
    Dependency to get K8s client instance.

    Returns:
        Configured K8s client
    """
    return K8sClient(config_path=settings.k8s_config_path)


@router.get("/namespaces")
async def get_namespaces(
    client: K8sClient = Depends(get_k8s_client),
) -> dict[str, Any]:
    """Get all namespaces in the cluster."""
    try:
        return await client.get_namespaces()
    except Exception as e:
        logger.error("Failed to get namespaces", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cluster-info")
async def get_cluster_info(
    client: K8sClient = Depends(get_k8s_client),
) -> dict[str, Any]:
    """Get cluster information."""
    try:
        return await client.get_cluster_info()
    except Exception as e:
        logger.error("Failed to get cluster info", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pods")
async def get_pods(
    namespace: str = Query(default="default"),
    label_selector: str | None = Query(default=None),
    client: K8sClient = Depends(get_k8s_client),
) -> dict[str, Any]:
    """Get pods in a namespace."""
    try:
        return await client.get_pods(namespace, label_selector)
    except Exception as e:
        logger.error("Failed to get pods", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pods/{pod_name}/logs")
async def get_pod_logs(
    pod_name: str,
    namespace: str = Query(default="default"),
    container: str | None = Query(default=None),
    tail_lines: int = Query(default=100),
    client: K8sClient = Depends(get_k8s_client),
) -> dict[str, str]:
    """Get logs from a pod."""
    try:
        logs = await client.get_pod_logs(pod_name, namespace, container, tail_lines)
        return {
            "pod": pod_name,
            "namespace": namespace,
            "container": container,
            "logs": logs,
        }
    except Exception as e:
        logger.error("Failed to get pod logs", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/deployments")
async def get_deployments(
    namespace: str = Query(default="default"),
    label_selector: str | None = Query(default=None),
    client: K8sClient = Depends(get_k8s_client),
) -> dict[str, Any]:
    """Get deployments in a namespace."""
    try:
        return await client.get_deployments(namespace, label_selector)
    except Exception as e:
        logger.error("Failed to get deployments", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/services")
async def get_services(
    namespace: str = Query(default="default"),
    label_selector: str | None = Query(default=None),
    client: K8sClient = Depends(get_k8s_client),
) -> dict[str, Any]:
    """Get services in a namespace."""
    try:
        return await client.get_services(namespace, label_selector)
    except Exception as e:
        logger.error("Failed to get services", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/events")
async def get_events(
    namespace: str = Query(default="default"),
    field_selector: str | None = Query(default=None),
    limit: int = Query(default=50),
    client: K8sClient = Depends(get_k8s_client),
) -> dict[str, Any]:
    """Get events in a namespace."""
    try:
        return await client.get_events(namespace, field_selector, limit)
    except Exception as e:
        logger.error("Failed to get events", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
