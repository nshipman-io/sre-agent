# SRE AI Agent

An AI-powered SRE agent that interacts with Kubernetes clusters to diagnose issues and recommend fixes using GPT-4 and documentation retrieval.

## Quick Start

### Docker (Recommended)
```bash
# 1. Set your OpenAI API key in .env
echo "OPENAI_API_KEY=sk-your-key-here" > .env

# 2. Start everything
./start.sh

# 3. Access the app
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Local Development
```bash
# Backend
cd backend
uv sync
uv run uvicorn app.main:app --reload  # Port 8000

# Frontend (separate terminal)
cd frontend
npm install
npm run dev  # Port 3000
```

## Architecture

```
Frontend (React) → Backend (FastAPI) → Kubernetes Cluster
                         ↓
                   ChromaDB + OpenAI
```

**Components**:
- **K8s Client**: Query and manage pods, deployments, services, logs, events (read and delete operations)
- **Document Service**: RAG system with ChromaDB + OpenAI embeddings
- **AI Agent**: Pydantic AI-powered agent with tool calling (GPT-4) and conversation history
- **Chat Interface**: React frontend with natural language queries and persistent conversation context

## Project Structure

```
sre-agent/
├── backend/
│   ├── app/
│   │   ├── api/              # REST endpoints (chat, k8s, documents)
│   │   ├── services/
│   │   │   ├── k8s_client.py       # Kubernetes integration
│   │   │   ├── document_service.py # ChromaDB + embeddings
│   │   │   └── ai_agent.py         # Pydantic AI agent
│   │   ├── config.py         # Settings (Pydantic)
│   │   └── main.py           # FastAPI app
│   ├── pyproject.toml        # Dependencies (UV)
│   └── .env                  # Backend config
├── frontend/
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── services/         # API clients
│   │   └── types/            # TypeScript types
│   └── package.json
├── docs/runbooks/            # Markdown runbooks for RAG
├── example-manifests/        # Test K8s resources for delete testing
│   ├── example-pod.yaml
│   ├── example-deployment.yaml
│   ├── example-service.yaml
│   └── example-configmap.yaml
├── docker-compose.yml
├── .env                      # Docker Compose config
└── start.sh / stop.sh
```

## Tech Stack

**Backend**: FastAPI, Pydantic AI, Kubernetes Client, ChromaDB, OpenAI, UV
**Frontend**: React, TypeScript, Vite, Tailwind CSS, TanStack Query

## Configuration

### Environment Variables

**`.env` (root)** - Docker Compose:
```bash
OPENAI_API_KEY=sk-your-key-here
```

**`backend/.env`** - Backend config:
```bash
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4-turbo-preview
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

K8S_CONFIG_PATH=                    # Empty for Docker, or /path/to/.kube/config
K8S_NAMESPACE=default

CHROMA_PERSIST_DIRECTORY=./data/chromadb
CHROMA_COLLECTION_NAME=runbooks
```

### Kubernetes Access

**Docker**: Mounts `~/.kube/config` automatically
**Local**: Set `K8S_CONFIG_PATH` in `backend/.env`
**In-cluster**: Leave `K8S_CONFIG_PATH` empty

## API Endpoints

**Base URL**: `http://localhost:8000`

### Chat
- `POST /v1/chat/message` - Send message to AI agent
- `POST /v1/chat/analyze-pods` - Proactive pod analysis

### Kubernetes
- `GET /v1/k8s/namespaces` - List namespaces
- `GET /v1/k8s/pods?namespace={ns}` - List pods
- `GET /v1/k8s/pods/{name}/logs?namespace={ns}` - Get logs
- `GET /v1/k8s/deployments?namespace={ns}` - List deployments
- `GET /v1/k8s/services?namespace={ns}` - List services
- `GET /v1/k8s/events?namespace={ns}` - List events
- `GET /v1/k8s/cluster-info` - Get cluster info

### Documents
- `POST /v1/docs/index` - Index single document
- `POST /v1/docs/index-directory` - Index directory
- `POST /v1/docs/search` - Search documents
- `GET /v1/docs/stats` - Collection stats
- `GET /v1/docs/{doc_id}` - Get document
- `DELETE /v1/docs/{doc_id}` - Delete document
- `POST /v1/docs/clear` - Clear collection

## Development

### Key Files to Modify

**Add K8s Tools**: `backend/app/services/ai_agent.py` - Add new tool methods
**Add API Endpoints**: `backend/app/api/` - Create new routers
**Frontend Components**: `frontend/src/components/` - React components
**API Client**: `frontend/src/services/api.ts` - Add API calls

### Adding a New Tool to AI Agent

```python
# In backend/app/services/ai_agent.py

# 1. Define input schema
class NewToolInput(BaseModel):
    """Input schema for new tool."""
    param: str = Field(description="Parameter description")
    namespace: str = Field(default="default", description="Kubernetes namespace")

# 2. Add method to K8sClient (if needed)
# In backend/app/services/k8s_client.py
async def new_k8s_operation(self, param: str, namespace: str = "default"):
    """Perform new K8s operation."""
    # Implementation here
    pass

# 3. Register tool with agent
# In backend/app/services/ai_agent.py _register_tools()
@self.agent.tool
async def new_tool(ctx: RunContext[SREDependencies], input: NewToolInput):
    """Tool description for the AI. Explain what it does and when to use it."""
    logger.info("Tool: new_tool", param=input.param)
    try:
        result = await ctx.deps.k8s_client.new_k8s_operation(
            param=input.param,
            namespace=input.namespace
        )
        return result
    except Exception as e:
        logger.error("new_tool failed", error=str(e))
        return {"error": str(e)}
```

### Indexing Runbooks

```bash
# Place .md files in docs/runbooks/, then:
curl -X POST http://localhost:8000/v1/docs/index-directory \
  -H "Content-Type: application/json" \
  -d '{"directory_path": "/app/docs/runbooks"}'  # Docker
  # or
  -d '{"directory_path": "./docs/runbooks"}'      # Local
```

## Features

### Read Operations
- Query pods, deployments, services, events, and namespaces
- Retrieve pod logs with filtering options
- Search runbooks and documentation using RAG
- Get cluster information and health status

### Write Operations (Destructive - Use with Caution)
- Delete pods with optional grace periods
- Delete deployments, services, statefulsets, daemonsets
- Delete configmaps and secrets
- All delete operations are logged for audit purposes

### Conversation Context
- Maintains full conversation history across messages
- Agent remembers previous requests and responses
- Supports multi-turn interactions for complex operations
- Context-aware confirmations and follow-ups

## Example Queries

### Read Operations
- "Show me all pods in the default namespace"
- "Why is my pod in CrashLoopBackOff?"
- "Get logs for pod xyz"
- "What deployments are having issues?"
- "Show recent events in production namespace"
- "How do I fix ImagePullBackOff?"

### Delete Operations (Destructive)
- "Delete the pod named test-nginx-pod in default namespace"
- "Remove the deployment broken-app from production"
- "Delete the service old-api in staging"
- "Delete the configmap test-config"

**Note**: The agent will request confirmation before performing delete operations and warn about permanent consequences.

## Testing

### Backend Tests
```bash
cd backend
uv run pytest

# Test backend manually
./test-backend.sh

# Verify health
curl http://localhost:8000/health
curl http://localhost:8000/v1/docs/stats
```

### Testing Delete Operations

Deploy test resources:
```bash
# Deploy all example manifests
kubectl apply -f example-manifests/

# Verify deployment
kubectl get all -n default -l environment=test
```

Test delete functionality through the agent:
```bash
# Via the chat interface, ask:
# "Delete the pod named test-nginx-pod in default namespace"
# "Remove the deployment test-nginx-deployment"
# "Delete the service test-nginx-service"
```

Clean up:
```bash
kubectl delete -f example-manifests/
```

See `example-manifests/README.md` for more testing scenarios.

## Docker Commands

```bash
./start.sh              # Start all services
./stop.sh               # Stop services
docker-compose logs -f  # View logs
docker-compose ps       # Check status
docker-compose down -v  # Remove everything including data
```

## Troubleshooting

**Backend won't start**: Check `backend/.env` has `OPENAI_API_KEY`
**K8s connection issues**: Verify `kubectl cluster-info` works
**No runbooks found**: Run index-directory endpoint
**ChromaDB errors**: Check `./data/chromadb` has write permissions
**Agent loses context**: Ensure frontend is sending `conversation_history` in chat requests
**Delete operations fail**: Verify RBAC permissions allow resource deletion in target namespace

## Safety Considerations

### Delete Operations
- All delete operations are **destructive and permanent**
- Agent is instructed to request confirmation before deletion
- All deletions are logged with structlog for audit trails
- Consider using RBAC to restrict delete permissions in production
- Test delete functionality in non-production namespaces first

### Best Practices
- Use label selectors (e.g., `environment=test`) for test resources
- Always specify namespace explicitly to avoid unintended deletions
- Review agent responses carefully before confirming destructive operations
- Monitor logs for unexpected delete operations
- Consider implementing approval workflows for production deletions

## Next Steps

1. Add your runbooks to `docs/runbooks/` and index them
2. Connect to your K8s cluster (set kubeconfig)
3. Test queries through the frontend at http://localhost:3000
4. Deploy test resources from `example-manifests/` to test delete functionality
5. Extend AI agent with custom tools in `ai_agent.py`
6. Add custom API endpoints in `backend/app/api/`
7. Implement RBAC policies to control agent permissions

## License

MIT
