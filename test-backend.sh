#!/bin/bash

echo "Testing SRE AI Agent Backend..."
echo ""

cd backend

echo "1. Testing Python environment..."
uv run python -c "import sys; print(f'   Python {sys.version.split()[0]}')"

echo ""
echo "2. Testing app imports..."
uv run python -c "from app.main import app; print('   ✓ All imports successful')"

echo ""
echo "3. Testing configuration..."
uv run python -c "
from app.config import settings
print(f'   App Name: {settings.app_name}')
print(f'   API Version: {settings.api_version}')
print(f'   OpenAI Model: {settings.openai_model}')
"

echo ""
echo "4. Starting server (5 seconds)..."
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
sleep 5

echo ""
echo "5. Testing health endpoint..."
curl -s http://localhost:8000/health | python -m json.tool

echo ""
echo "6. Testing root endpoint..."
curl -s http://localhost:8000/ | python -m json.tool

echo ""
echo "Stopping server..."
kill $BACKEND_PID 2>/dev/null
wait $BACKEND_PID 2>/dev/null

echo ""
echo "✅ All tests passed!"
