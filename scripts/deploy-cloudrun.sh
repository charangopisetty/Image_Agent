#!/usr/bin/env bash
# Deploy image_agent to Google Cloud Run.
#
# Prerequisites:
#   gcloud auth login
#   gcloud config set project YOUR_PROJECT_ID
#   export GROQ_API_KEY=...
#   export API_KEY=...          # shared key for all API clients
#
# Usage:
#   ./scripts/deploy-cloudrun.sh [SERVICE_NAME] [REGION]

set -euo pipefail

SERVICE_NAME="${1:-image-agent}"
REGION="${2:-us-central1}"
PROJECT_ID="$(gcloud config get-value project 2>/dev/null)"

if [[ -z "${PROJECT_ID}" || "${PROJECT_ID}" == "(unset)" ]]; then
  echo "Set a GCP project: gcloud config set project YOUR_PROJECT_ID"
  exit 1
fi

if [[ -z "${GROQ_API_KEY:-}" ]]; then
  echo "Export GROQ_API_KEY before deploying."
  exit 1
fi

if [[ -z "${API_KEY:-}" ]]; then
  echo "Export API_KEY before deploying (shared client API key)."
  exit 1
fi

IMAGE="gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest"

echo "Building ${IMAGE}..."
gcloud builds submit --tag "${IMAGE}" .

echo "Deploying ${SERVICE_NAME} to Cloud Run (${REGION})..."
gcloud run deploy "${SERVICE_NAME}" \
  --image "${IMAGE}" \
  --region "${REGION}" \
  --platform managed \
  --allow-unauthenticated \
  --port 8080 \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --min-instances 0 \
  --max-instances 10 \
  --set-env-vars "GROQ_API_KEY=${GROQ_API_KEY},API_KEY=${API_KEY},MODEL=${MODEL:-groq/qwen/qwen3-32b},VISION_MODEL=${VISION_MODEL:-groq/meta-llama/llama-4-scout-17b-16e-instruct}"

echo "Done. Service URL:"
gcloud run services describe "${SERVICE_NAME}" --region "${REGION}" --format='value(status.url)'
