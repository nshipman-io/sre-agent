"""Kubernetes client service for cluster interaction."""
from typing import Any
import structlog
from kubernetes import client, config
from kubernetes.client.rest import ApiException

logger = structlog.get_logger()


class K8sClient:
    """Kubernetes client for querying cluster resources."""

    def __init__(self, config_path: str | None = None):
        """
        Initialize K8s client.

        Args:
            config_path: Path to kubeconfig file. If None, uses in-cluster config.
        """
        self.config_path = config_path
        self._initialize_client()

    def _initialize_client(self) -> None:
        """Initialize Kubernetes client configuration."""
        try:
            if self.config_path:
                config.load_kube_config(config_file=self.config_path)
                logger.info("Loaded kubeconfig", path=self.config_path)
            else:
                config.load_incluster_config()
                logger.info("Loaded in-cluster config")

            self.core_v1 = client.CoreV1Api()
            self.apps_v1 = client.AppsV1Api()
            self.batch_v1 = client.BatchV1Api()
            self.networking_v1 = client.NetworkingV1Api()

        except Exception as e:
            logger.error("Failed to initialize K8s client", error=str(e))
            raise

    async def get_pods(
        self, namespace: str = "default", label_selector: str | None = None
    ) -> dict[str, Any]:
        """
        Get pods in a namespace.

        Args:
            namespace: Kubernetes namespace
            label_selector: Label selector for filtering pods

        Returns:
            Dictionary containing pod information
        """
        try:
            pods = self.core_v1.list_namespaced_pod(
                namespace=namespace, label_selector=label_selector
            )

            pod_list = []
            for pod in pods.items:
                pod_info = {
                    "name": pod.metadata.name,
                    "namespace": pod.metadata.namespace,
                    "status": pod.status.phase,
                    "conditions": [
                        {
                            "type": c.type,
                            "status": c.status,
                            "reason": c.reason,
                            "message": c.message,
                        }
                        for c in (pod.status.conditions or [])
                    ],
                    "containers": [
                        {
                            "name": c.name,
                            "image": c.image,
                            "ready": any(
                                cs.name == c.name and cs.ready
                                for cs in (pod.status.container_statuses or [])
                            ),
                            "restart_count": next(
                                (
                                    cs.restart_count
                                    for cs in (pod.status.container_statuses or [])
                                    if cs.name == c.name
                                ),
                                0,
                            ),
                        }
                        for c in pod.spec.containers
                    ],
                    "node": pod.spec.node_name,
                    "created_at": pod.metadata.creation_timestamp.isoformat(),
                }
                pod_list.append(pod_info)

            logger.info(
                "Retrieved pods",
                namespace=namespace,
                count=len(pod_list),
                label_selector=label_selector,
            )
            return {"pods": pod_list, "count": len(pod_list)}

        except ApiException as e:
            logger.error("Failed to get pods", error=str(e), namespace=namespace)
            raise

    async def get_pod_logs(
        self,
        pod_name: str,
        namespace: str = "default",
        container: str | None = None,
        tail_lines: int = 100,
    ) -> str:
        """
        Get logs from a pod.

        Args:
            pod_name: Name of the pod
            namespace: Kubernetes namespace
            container: Container name (if pod has multiple containers)
            tail_lines: Number of lines to retrieve from the end

        Returns:
            Pod logs as string
        """
        try:
            logs = self.core_v1.read_namespaced_pod_log(
                name=pod_name,
                namespace=namespace,
                container=container,
                tail_lines=tail_lines,
            )
            logger.info(
                "Retrieved pod logs",
                pod=pod_name,
                namespace=namespace,
                container=container,
            )
            return logs

        except ApiException as e:
            logger.error(
                "Failed to get pod logs",
                error=str(e),
                pod=pod_name,
                namespace=namespace,
            )
            raise

    async def get_deployments(
        self, namespace: str = "default", label_selector: str | None = None
    ) -> dict[str, Any]:
        """
        Get deployments in a namespace.

        Args:
            namespace: Kubernetes namespace
            label_selector: Label selector for filtering deployments

        Returns:
            Dictionary containing deployment information
        """
        try:
            deployments = self.apps_v1.list_namespaced_deployment(
                namespace=namespace, label_selector=label_selector
            )

            deployment_list = []
            for deploy in deployments.items:
                deployment_info = {
                    "name": deploy.metadata.name,
                    "namespace": deploy.metadata.namespace,
                    "replicas": {
                        "desired": deploy.spec.replicas,
                        "current": deploy.status.replicas or 0,
                        "ready": deploy.status.ready_replicas or 0,
                        "updated": deploy.status.updated_replicas or 0,
                        "available": deploy.status.available_replicas or 0,
                    },
                    "conditions": [
                        {
                            "type": c.type,
                            "status": c.status,
                            "reason": c.reason,
                            "message": c.message,
                        }
                        for c in (deploy.status.conditions or [])
                    ],
                    "strategy": deploy.spec.strategy.type,
                    "created_at": deploy.metadata.creation_timestamp.isoformat(),
                }
                deployment_list.append(deployment_info)

            logger.info(
                "Retrieved deployments",
                namespace=namespace,
                count=len(deployment_list),
                label_selector=label_selector,
            )
            return {"deployments": deployment_list, "count": len(deployment_list)}

        except ApiException as e:
            logger.error(
                "Failed to get deployments", error=str(e), namespace=namespace
            )
            raise

    async def get_services(
        self, namespace: str = "default", label_selector: str | None = None
    ) -> dict[str, Any]:
        """
        Get services in a namespace.

        Args:
            namespace: Kubernetes namespace
            label_selector: Label selector for filtering services

        Returns:
            Dictionary containing service information
        """
        try:
            services = self.core_v1.list_namespaced_service(
                namespace=namespace, label_selector=label_selector
            )

            service_list = []
            for svc in services.items:
                service_info = {
                    "name": svc.metadata.name,
                    "namespace": svc.metadata.namespace,
                    "type": svc.spec.type,
                    "cluster_ip": svc.spec.cluster_ip,
                    "external_ips": svc.spec.external_i_ps or [],
                    "ports": [
                        {
                            "name": p.name,
                            "port": p.port,
                            "target_port": str(p.target_port),
                            "protocol": p.protocol,
                        }
                        for p in (svc.spec.ports or [])
                    ],
                    "selector": svc.spec.selector or {},
                    "created_at": svc.metadata.creation_timestamp.isoformat(),
                }
                service_list.append(service_info)

            logger.info(
                "Retrieved services",
                namespace=namespace,
                count=len(service_list),
                label_selector=label_selector,
            )
            return {"services": service_list, "count": len(service_list)}

        except ApiException as e:
            logger.error("Failed to get services", error=str(e), namespace=namespace)
            raise

    async def get_events(
        self,
        namespace: str = "default",
        field_selector: str | None = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        """
        Get events in a namespace.

        Args:
            namespace: Kubernetes namespace
            field_selector: Field selector for filtering events
            limit: Maximum number of events to retrieve

        Returns:
            Dictionary containing event information
        """
        try:
            events = self.core_v1.list_namespaced_event(
                namespace=namespace, field_selector=field_selector, limit=limit
            )

            event_list = []
            for event in events.items:
                event_info = {
                    "name": event.metadata.name,
                    "namespace": event.metadata.namespace,
                    "type": event.type,
                    "reason": event.reason,
                    "message": event.message,
                    "involved_object": {
                        "kind": event.involved_object.kind,
                        "name": event.involved_object.name,
                        "namespace": event.involved_object.namespace,
                    },
                    "count": event.count,
                    "first_timestamp": (
                        event.first_timestamp.isoformat()
                        if event.first_timestamp
                        else None
                    ),
                    "last_timestamp": (
                        event.last_timestamp.isoformat()
                        if event.last_timestamp
                        else None
                    ),
                }
                event_list.append(event_info)

            # Sort by last timestamp, most recent first
            event_list.sort(
                key=lambda x: x["last_timestamp"] or "", reverse=True
            )

            logger.info(
                "Retrieved events",
                namespace=namespace,
                count=len(event_list),
                field_selector=field_selector,
            )
            return {"events": event_list, "count": len(event_list)}

        except ApiException as e:
            logger.error("Failed to get events", error=str(e), namespace=namespace)
            raise

    async def get_namespaces(self) -> dict[str, Any]:
        """
        Get all namespaces in the cluster.

        Returns:
            Dictionary containing namespace information
        """
        try:
            namespaces = self.core_v1.list_namespace()

            namespace_list = [
                {
                    "name": ns.metadata.name,
                    "status": ns.status.phase,
                    "created_at": ns.metadata.creation_timestamp.isoformat(),
                    "labels": ns.metadata.labels or {},
                }
                for ns in namespaces.items
            ]

            logger.info("Retrieved namespaces", count=len(namespace_list))
            return {"namespaces": namespace_list, "count": len(namespace_list)}

        except ApiException as e:
            logger.error("Failed to get namespaces", error=str(e))
            raise

    async def get_cluster_info(self) -> dict[str, Any]:
        """
        Get general cluster information.

        Returns:
            Dictionary containing cluster information
        """
        try:
            # Get nodes
            nodes = self.core_v1.list_node()
            node_list = [
                {
                    "name": node.metadata.name,
                    "status": next(
                        (
                            c.type
                            for c in node.status.conditions
                            if c.status == "True"
                        ),
                        "Unknown",
                    ),
                    "roles": list(
                        {
                            label.split("/")[1]
                            for label in (node.metadata.labels or {}).keys()
                            if "node-role.kubernetes.io" in label
                        }
                    ),
                    "version": node.status.node_info.kubelet_version,
                    "os": f"{node.status.node_info.os_image}",
                    "kernel": node.status.node_info.kernel_version,
                }
                for node in nodes.items
            ]

            # Get cluster version
            version = await self._get_version()

            logger.info("Retrieved cluster info", node_count=len(node_list))
            return {
                "nodes": node_list,
                "node_count": len(node_list),
                "version": version,
            }

        except ApiException as e:
            logger.error("Failed to get cluster info", error=str(e))
            raise

    async def _get_version(self) -> dict[str, str]:
        """Get Kubernetes version information."""
        try:
            version_api = client.VersionApi()
            version = version_api.get_code()
            return {
                "major": version.major,
                "minor": version.minor,
                "git_version": version.git_version,
            }
        except Exception as e:
            logger.error("Failed to get version", error=str(e))
            return {"major": "unknown", "minor": "unknown", "git_version": "unknown"}
