#!/bin/bash

set -e

PROJECT_ID="haratch-ocr"
REGION="us-central1"

echo "🔧 Setting up GCP project for Haratch OCR..."

echo "📋 Setting project..."
gcloud config set project $PROJECT_ID

echo "🔑 Enabling required APIs..."
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable storage.googleapis.com

echo "👤 Creating service account..."
gcloud iam service-accounts create haratch-ocr \
    --display-name="Haratch OCR Service Account" \
    --description="Service account for Haratch OCR Cloud Run service"

echo "🔐 Granting permissions..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:haratch-ocr@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/storage.admin"
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:haratch-ocr@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/run.invoker"

echo "✅ GCP setup complete!"
echo "🚀 You can now run ./deploy.sh to deploy the application"
