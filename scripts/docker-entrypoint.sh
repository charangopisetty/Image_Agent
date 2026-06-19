#!/bin/sh
set -e

PORT="${PORT:-8080}"

echo "Starting Image Agent API on :${PORT}"
exec uv run uvicorn image_agent.api:app --host 0.0.0.0 --port "${PORT}"
