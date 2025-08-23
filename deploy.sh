#!/bin/bash

set -e

PROJECT_ID="haratch-ocr"
REGION="us-central1"
SERVICE_NAME="haratch-ocr"

echo "🚀 Deploying Haratch OCR to GCP Cloud Run..."

echo "📦 Building and pushing Docker image..."
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME

echo "🔧 Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --memory 8Gi \
  --cpu 4 \
  --timeout 3600 \
  --concurrency 1 \
  --service-account haratch-ocr@$PROJECT_ID.iam.gserviceaccount.com

echo "✅ Deployment complete!"
echo "🌐 Service URL: $(gcloud run services describe $SERVICE_NAME --region=$REGION --format='value(status.url)')"
