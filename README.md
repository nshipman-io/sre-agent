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
- **K8s Client**: Query pods, deployments, services, logs, events
- **Document Service**: RAG system with ChromaDB + OpenAI embeddings
- **AI Agent**: Pydantic AI-powered agent with tool calling (GPT-4)
- **Chat Interface**: React frontend with natural language queries

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

class NewToolInput(BaseModel):
    """Input schema for new tool."""
    param: str = Field(description="Parameter description")

@self.agent.tool
async def new_tool(ctx: RunContext[SREDependencies], input: NewToolInput):
    """Tool description for the AI."""
    # Access dependencies
    result = await ctx.deps.k8s_client.some_method(input.param)
    return result
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

## Example Queries

- "Show me all pods in the default namespace"
- "Why is my pod in CrashLoopBackOff?"
- "Get logs for pod xyz"
- "What deployments are having issues?"
- "Show recent events in production namespace"
- "How do I fix ImagePullBackOff?"

## Testing

```bash
# Backend
cd backend
uv run pytest

# Test backend manually
./test-backend.sh

# Verify health
curl http://localhost:8000/health
curl http://localhost:8000/v1/docs/stats
```

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

## Next Steps

1. Add your runbooks to `docs/runbooks/` and index them
2. Connect to your K8s cluster (set kubeconfig)
3. Test queries through the frontend at http://localhost:3000
4. Extend AI agent with custom tools in `ai_agent.py`
5. Add custom API endpoints in `backend/app/api/`

## License

MIT
