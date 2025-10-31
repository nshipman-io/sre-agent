"""AI agent service for SRE diagnostics and recommendations using Pydantic AI."""
import json
from typing import Any
from dataclasses import dataclass

import structlog
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext

from app.services.k8s_client import K8sClient
from app.services.document_service import DocumentService

logger = structlog.get_logger()


# Pydantic models for tool inputs
class GetPodsInput(BaseModel):
    """Input schema for get_pods tool."""

    namespace: str = Field(default="default", description="The Kubernetes namespace")
    label_selector: str | None = Field(
        default=None, description="Label selector for filtering pods (e.g., 'app=nginx')"
    )


class GetPodLogsInput(BaseModel):
    """Input schema for get_pod_logs tool."""

    pod_name: str = Field(description="Name of the pod")
    namespace: str = Field(default="default", description="The Kubernetes namespace")
    container: str | None = Field(
        default=None, description="Container name (if pod has multiple containers)"
    )
    tail_lines: int = Field(default=100, description="Number of lines to retrieve")


class GetDeploymentsInput(BaseModel):
    """Input schema for get_deployments tool."""

    namespace: str = Field(default="default", description="The Kubernetes namespace")
    label_selector: str | None = Field(
        default=None, description="Label selector for filtering deployments"
    )


class GetEventsInput(BaseModel):
    """Input schema for get_events tool."""

    namespace: str = Field(default="default", description="The Kubernetes namespace")
    field_selector: str | None = Field(
        default=None, description="Field selector for filtering events"
    )
    limit: int = Field(default=50, description="Maximum number of events to retrieve")


class SearchRunbooksInput(BaseModel):
    """Input schema for search_runbooks tool."""

    query: str = Field(description="Search query for finding relevant documentation")
    n_results: int = Field(default=3, description="Number of results to return")


class DeletePodInput(BaseModel):
    """Input schema for delete_pod tool."""

    pod_name: str = Field(description="Name of the pod to delete")
    namespace: str = Field(default="default", description="The Kubernetes namespace")
    grace_period_seconds: int | None = Field(
        default=None, description="Grace period for pod termination in seconds"
    )


class DeleteDeploymentInput(BaseModel):
    """Input schema for delete_deployment tool."""

    deployment_name: str = Field(description="Name of the deployment to delete")
    namespace: str = Field(default="default", description="The Kubernetes namespace")
    grace_period_seconds: int | None = Field(
        default=None, description="Grace period for resource termination in seconds"
    )


class DeleteServiceInput(BaseModel):
    """Input schema for delete_service tool."""

    service_name: str = Field(description="Name of the service to delete")
    namespace: str = Field(default="default", description="The Kubernetes namespace")


class DeleteStatefulSetInput(BaseModel):
    """Input schema for delete_statefulset tool."""

    statefulset_name: str = Field(description="Name of the statefulset to delete")
    namespace: str = Field(default="default", description="The Kubernetes namespace")
    grace_period_seconds: int | None = Field(
        default=None, description="Grace period for resource termination in seconds"
    )


class DeleteDaemonSetInput(BaseModel):
    """Input schema for delete_daemonset tool."""

    daemonset_name: str = Field(description="Name of the daemonset to delete")
    namespace: str = Field(default="default", description="The Kubernetes namespace")
    grace_period_seconds: int | None = Field(
        default=None, description="Grace period for resource termination in seconds"
    )


class DeleteConfigMapInput(BaseModel):
    """Input schema for delete_configmap tool."""

    configmap_name: str = Field(description="Name of the configmap to delete")
    namespace: str = Field(default="default", description="The Kubernetes namespace")


class DeleteSecretInput(BaseModel):
    """Input schema for delete_secret tool."""

    secret_name: str = Field(description="Name of the secret to delete")
    namespace: str = Field(default="default", description="The Kubernetes namespace")


@dataclass
class SREDependencies:
    """Dependencies injected into agent tools."""

    k8s_client: K8sClient
    document_service: DocumentService
    default_namespace: str = "default"


class SREAgent:
    """AI agent for SRE diagnostics and recommendations using Pydantic AI."""

    def __init__(
        self,
        openai_api_key: str,
        k8s_client: K8sClient,
        document_service: DocumentService,
        model: str = "gpt-4-turbo-preview",
    ):
        """
        Initialize SRE agent.

        Args:
            openai_api_key: OpenAI API key
            k8s_client: Kubernetes client instance
            document_service: Document service instance
            model: OpenAI model to use
        """
        self.k8s_client = k8s_client
        self.document_service = document_service
        self.model = model

        # Create Pydantic AI agent with OpenAI
        self.agent = Agent(
            model=f"openai:{model}",
            deps_type=SREDependencies,
            system_prompt=(
                "You are an expert SRE (Site Reliability Engineer) AI assistant. "
                "Your role is to help diagnose and resolve Kubernetes cluster issues.\n\n"
                "You have access to tools to:\n"
                "1. Query Kubernetes resources (pods, deployments, services, events)\n"
                "2. Retrieve pod logs\n"
                "3. Search runbooks and documentation\n"
                "4. Delete Kubernetes resources (pods, deployments, services, statefulsets, daemonsets, configmaps, secrets)\n\n"
                "IMPORTANT: When the user mentions a specific namespace in their message "
                "(e.g., 'kube-system', 'default', 'production'), use that namespace in your tool calls. "
                "The default namespace provided in the context is just a fallback.\n\n"
                "When analyzing issues:\n"
                "1. Gather relevant cluster data using available tools\n"
                "2. Search runbooks for similar issues and solutions\n"
                "3. Provide clear, actionable recommendations\n"
                "4. Explain the root cause when possible\n"
                "5. Suggest preventive measures\n\n"
                "IMPORTANT: For delete operations:\n"
                "1. Only use delete tools when explicitly requested by the user\n"
                "2. Always confirm the resource name and namespace before deletion\n"
                "3. Warn the user that deletion is permanent and cannot be undone\n"
                "4. Consider the impact on dependent resources\n"
                "5. Use appropriate grace periods when terminating pods\n\n"
                "Be thorough but concise. Prioritize safety - suggest read-only operations first."
            ),
        )

        # Register tools
        self._register_tools()

        logger.info("Initialized SRE agent with Pydantic AI", model=model)

    def _register_tools(self):
        """Register all tools with the agent."""

        @self.agent.tool
        async def get_pods(
            ctx: RunContext[SREDependencies], input: GetPodsInput
        ) -> dict[str, Any]:
            """Get information about pods in a Kubernetes namespace."""
            logger.info(
                "Tool: get_pods",
                namespace=input.namespace,
                label_selector=input.label_selector,
            )
            try:
                result = await ctx.deps.k8s_client.get_pods(
                    namespace=input.namespace, label_selector=input.label_selector
                )
                return result
            except Exception as e:
                logger.error("get_pods failed", error=str(e))
                return {"error": str(e)}

        @self.agent.tool
        async def get_pod_logs(
            ctx: RunContext[SREDependencies], input: GetPodLogsInput
        ) -> dict[str, Any]:
            """Get logs from a specific pod."""
            logger.info(
                "Tool: get_pod_logs",
                pod=input.pod_name,
                namespace=input.namespace,
                container=input.container,
            )
            try:
                logs = await ctx.deps.k8s_client.get_pod_logs(
                    pod_name=input.pod_name,
                    namespace=input.namespace,
                    container=input.container,
                    tail_lines=input.tail_lines,
                )
                return {"logs": logs, "pod_name": input.pod_name}
            except Exception as e:
                logger.error("get_pod_logs failed", error=str(e))
                return {"error": str(e)}

        @self.agent.tool
        async def get_deployments(
            ctx: RunContext[SREDependencies], input: GetDeploymentsInput
        ) -> dict[str, Any]:
            """Get information about deployments in a Kubernetes namespace."""
            logger.info(
                "Tool: get_deployments",
                namespace=input.namespace,
                label_selector=input.label_selector,
            )
            try:
                result = await ctx.deps.k8s_client.get_deployments(
                    namespace=input.namespace, label_selector=input.label_selector
                )
                return result
            except Exception as e:
                logger.error("get_deployments failed", error=str(e))
                return {"error": str(e)}

        @self.agent.tool
        async def get_events(
            ctx: RunContext[SREDependencies], input: GetEventsInput
        ) -> dict[str, Any]:
            """Get recent events in a Kubernetes namespace."""
            logger.info(
                "Tool: get_events",
                namespace=input.namespace,
                field_selector=input.field_selector,
            )
            try:
                result = await ctx.deps.k8s_client.get_events(
                    namespace=input.namespace,
                    field_selector=input.field_selector,
                    limit=input.limit,
                )
                return result
            except Exception as e:
                logger.error("get_events failed", error=str(e))
                return {"error": str(e)}

        @self.agent.tool
        async def search_runbooks(
            ctx: RunContext[SREDependencies], input: SearchRunbooksInput
        ) -> dict[str, Any]:
            """Search runbooks and documentation for relevant information."""
            logger.info("Tool: search_runbooks", query=input.query)
            try:
                results = await ctx.deps.document_service.search_documents(
                    query=input.query, n_results=input.n_results
                )
                return {"results": results, "query": input.query}
            except Exception as e:
                logger.error("search_runbooks failed", error=str(e))
                return {"error": str(e)}

        @self.agent.tool
        async def delete_pod(
            ctx: RunContext[SREDependencies], input: DeletePodInput
        ) -> dict[str, Any]:
            """Delete a pod from a Kubernetes namespace. Use with caution - this is a destructive operation."""
            logger.info(
                "Tool: delete_pod",
                pod=input.pod_name,
                namespace=input.namespace,
                grace_period=input.grace_period_seconds,
            )
            try:
                result = await ctx.deps.k8s_client.delete_pod(
                    pod_name=input.pod_name,
                    namespace=input.namespace,
                    grace_period_seconds=input.grace_period_seconds,
                )
                return result
            except Exception as e:
                logger.error("delete_pod failed", error=str(e))
                return {"error": str(e), "status": "failed"}

        @self.agent.tool
        async def delete_deployment(
            ctx: RunContext[SREDependencies], input: DeleteDeploymentInput
        ) -> dict[str, Any]:
            """Delete a deployment from a Kubernetes namespace. Use with caution - this is a destructive operation."""
            logger.info(
                "Tool: delete_deployment",
                deployment=input.deployment_name,
                namespace=input.namespace,
                grace_period=input.grace_period_seconds,
            )
            try:
                result = await ctx.deps.k8s_client.delete_deployment(
                    deployment_name=input.deployment_name,
                    namespace=input.namespace,
                    grace_period_seconds=input.grace_period_seconds,
                )
                return result
            except Exception as e:
                logger.error("delete_deployment failed", error=str(e))
                return {"error": str(e), "status": "failed"}

        @self.agent.tool
        async def delete_service(
            ctx: RunContext[SREDependencies], input: DeleteServiceInput
        ) -> dict[str, Any]:
            """Delete a service from a Kubernetes namespace. Use with caution - this is a destructive operation."""
            logger.info(
                "Tool: delete_service",
                service=input.service_name,
                namespace=input.namespace,
            )
            try:
                result = await ctx.deps.k8s_client.delete_service(
                    service_name=input.service_name,
                    namespace=input.namespace,
                )
                return result
            except Exception as e:
                logger.error("delete_service failed", error=str(e))
                return {"error": str(e), "status": "failed"}

        @self.agent.tool
        async def delete_statefulset(
            ctx: RunContext[SREDependencies], input: DeleteStatefulSetInput
        ) -> dict[str, Any]:
            """Delete a statefulset from a Kubernetes namespace. Use with caution - this is a destructive operation."""
            logger.info(
                "Tool: delete_statefulset",
                statefulset=input.statefulset_name,
                namespace=input.namespace,
                grace_period=input.grace_period_seconds,
            )
            try:
                result = await ctx.deps.k8s_client.delete_statefulset(
                    statefulset_name=input.statefulset_name,
                    namespace=input.namespace,
                    grace_period_seconds=input.grace_period_seconds,
                )
                return result
            except Exception as e:
                logger.error("delete_statefulset failed", error=str(e))
                return {"error": str(e), "status": "failed"}

        @self.agent.tool
        async def delete_daemonset(
            ctx: RunContext[SREDependencies], input: DeleteDaemonSetInput
        ) -> dict[str, Any]:
            """Delete a daemonset from a Kubernetes namespace. Use with caution - this is a destructive operation."""
            logger.info(
                "Tool: delete_daemonset",
                daemonset=input.daemonset_name,
                namespace=input.namespace,
                grace_period=input.grace_period_seconds,
            )
            try:
                result = await ctx.deps.k8s_client.delete_daemonset(
                    daemonset_name=input.daemonset_name,
                    namespace=input.namespace,
                    grace_period_seconds=input.grace_period_seconds,
                )
                return result
            except Exception as e:
                logger.error("delete_daemonset failed", error=str(e))
                return {"error": str(e), "status": "failed"}

        @self.agent.tool
        async def delete_configmap(
            ctx: RunContext[SREDependencies], input: DeleteConfigMapInput
        ) -> dict[str, Any]:
            """Delete a configmap from a Kubernetes namespace. Use with caution - this is a destructive operation."""
            logger.info(
                "Tool: delete_configmap",
                configmap=input.configmap_name,
                namespace=input.namespace,
            )
            try:
                result = await ctx.deps.k8s_client.delete_configmap(
                    configmap_name=input.configmap_name,
                    namespace=input.namespace,
                )
                return result
            except Exception as e:
                logger.error("delete_configmap failed", error=str(e))
                return {"error": str(e), "status": "failed"}

        @self.agent.tool
        async def delete_secret(
            ctx: RunContext[SREDependencies], input: DeleteSecretInput
        ) -> dict[str, Any]:
            """Delete a secret from a Kubernetes namespace. Use with caution - this is a destructive operation."""
            logger.info(
                "Tool: delete_secret",
                secret=input.secret_name,
                namespace=input.namespace,
            )
            try:
                result = await ctx.deps.k8s_client.delete_secret(
                    secret_name=input.secret_name,
                    namespace=input.namespace,
                )
                return result
            except Exception as e:
                logger.error("delete_secret failed", error=str(e))
                return {"error": str(e), "status": "failed"}

    async def chat(
        self,
        user_message: str,
        conversation_history: list[dict[str, str]] | None = None,
        namespace: str = "default",
    ) -> dict[str, Any]:
        """
        Process a user message and generate a response.

        Args:
            user_message: User's message
            conversation_history: Previous conversation messages in format [{"role": "user"|"assistant", "content": "..."}]
            namespace: Default Kubernetes namespace to use

        Returns:
            Agent response with recommendations
        """
        deps = SREDependencies(
            k8s_client=self.k8s_client,
            document_service=self.document_service,
            default_namespace=namespace,
        )

        try:
            # Build conversation context from history
            # Skip the initial greeting message (first assistant message) if present
            filtered_history = []
            if conversation_history and len(conversation_history) > 0:
                for msg in conversation_history:
                    # Skip initial greeting
                    if msg.get("role") == "assistant" and "Hello! I'm your SRE AI Assistant" in msg.get("content", ""):
                        continue
                    filtered_history.append(msg)

            # Build the full prompt with conversation context
            if filtered_history:
                # Create a rich conversation context
                conversation_context = []
                conversation_context.append(f"[Current default namespace: {namespace}]")
                conversation_context.append("\n[Previous conversation in this session:]")

                for msg in filtered_history:
                    role = msg.get("role", "user")
                    content = msg.get("content", "")
                    if role == "user":
                        conversation_context.append(f"\nUser said: {content}")
                    elif role == "assistant":
                        conversation_context.append(f"\nYou (assistant) previously responded: {content}")

                conversation_context.append(f"\n\n[Current user message in this ongoing conversation:]")
                conversation_context.append(user_message)

                enhanced_message = "\n".join(conversation_context)
            else:
                # No history, just add namespace context
                enhanced_message = f"[Current default namespace: {namespace}]\n\n{user_message}"

            # Run the agent
            result = await self.agent.run(enhanced_message, deps=deps)

            usage = result.usage()
            logger.info(
                "Generated response",
                message_length=len(str(result.output)),
                tokens=f"in={usage.input_tokens} out={usage.output_tokens}",
            )

            # Extract tool calls from result for backwards compatibility
            tool_calls_made = []
            if hasattr(result, "all_messages"):
                for msg in result.all_messages():
                    if hasattr(msg, "parts"):
                        for part in msg.parts:
                            if hasattr(part, "tool_name"):
                                # Handle args - could be dict, Pydantic model, or other
                                args = {}
                                if hasattr(part, "args"):
                                    if hasattr(part.args, "model_dump"):
                                        args = part.args.model_dump()
                                    elif isinstance(part.args, dict):
                                        args = part.args
                                    else:
                                        args = {"raw": str(part.args)}

                                tool_calls_made.append(
                                    {
                                        "tool": part.tool_name,
                                        "arguments": args,
                                    }
                                )

            return {
                "response": str(result.output),
                "tool_calls": tool_calls_made,
                "model": self.model,
                "usage": {
                    "input_tokens": usage.input_tokens,
                    "output_tokens": usage.output_tokens,
                    "total_tokens": usage.input_tokens + usage.output_tokens,
                } if usage else None,
            }

        except Exception as e:
            logger.error("Failed to generate response", error=str(e))
            raise

    async def analyze_pod_issues(
        self, namespace: str = "default", label_selector: str | None = None
    ) -> dict[str, Any]:
        """
        Proactively analyze pods for potential issues.

        Args:
            namespace: Kubernetes namespace
            label_selector: Label selector for filtering pods

        Returns:
            Analysis results with recommendations
        """
        try:
            # Get pods
            pods_data = await self.k8s_client.get_pods(namespace, label_selector)

            # Identify problematic pods
            issues = []
            for pod in pods_data["pods"]:
                if pod["status"] != "Running":
                    issues.append(
                        {
                            "pod": pod["name"],
                            "status": pod["status"],
                            "conditions": pod["conditions"],
                        }
                    )

                # Check for high restart counts
                for container in pod["containers"]:
                    if container["restart_count"] > 5:
                        issues.append(
                            {
                                "pod": pod["name"],
                                "container": container["name"],
                                "issue": "high_restart_count",
                                "restart_count": container["restart_count"],
                            }
                        )

            if not issues:
                return {
                    "status": "healthy",
                    "message": f"All pods in namespace '{namespace}' appear healthy",
                    "pods_checked": len(pods_data["pods"]),
                }

            # Use AI to analyze issues
            issue_summary = json.dumps(issues, indent=2)
            analysis_prompt = f"""Analyze these Kubernetes pod issues and provide recommendations:

Issues found:
{issue_summary}

Namespace: {namespace}

Please provide:
1. Root cause analysis for each issue
2. Recommended actions to resolve
3. Preventive measures"""

            response = await self.chat(analysis_prompt, namespace=namespace)

            return {
                "status": "issues_found",
                "issues": issues,
                "analysis": response["response"],
                "tool_calls": response["tool_calls"],
            }

        except Exception as e:
            logger.error("Failed to analyze pod issues", error=str(e))
            raise
