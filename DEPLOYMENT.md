# Deployment Guide for Google Cloud Run

This guide will help you deploy the Agent-Will-Smith API to Google Cloud Run via Google Artifact Registry (GCR).

## Prerequisites

1. **Google Cloud SDK (gcloud CLI)** installed and configured
   ```bash
   # Install gcloud CLI if not already installed
   # https://cloud.google.com/sdk/docs/install
   
   # Authenticate
   gcloud auth login
   gcloud auth application-default login
   ```

2. **Docker** installed and running

3. **Access to the GCP project**: `uat-env-888888`

4. **Artifact Registry repository** already created:
   - Region: `asia-east1`
   - Repository: `docker-repo`

## Quick Deployment

### Option 1: Using the Deployment Script (Recommended)

```bash
./deploy-cloudrun.sh
```

The script will:
1. Build the Docker image
2. Tag it with `latest` and a timestamp
3. Push to Artifact Registry
4. Optionally deploy to Cloud Run

### Option 2: Manual Deployment

#### Step 1: Configure Docker Authentication

```bash
gcloud auth configure-docker asia-east1-docker.pkg.dev
```

#### Step 2: Set GCP Project

```bash
gcloud config set project uat-env-888888
```

#### Step 3: Build the Docker Image

**Important**: Build for `linux/amd64` platform (required for Cloud Run):

```bash
docker build --platform linux/amd64 -t asia-east1-docker.pkg.dev/uat-env-888888/docker-repo/agent-will-smith:latest .
```

#### Step 4: Push to Artifact Registry

```bash
docker push asia-east1-docker.pkg.dev/uat-env-888888/docker-repo/agent-will-smith:latest
```

#### Step 5: Deploy to Cloud Run

**Using Secret Manager (Recommended - matches previous deployment):**

```bash
gcloud run deploy agent-will-smith \
  --image asia-east1-docker.pkg.dev/uat-env-888888/docker-repo/agent-will-smith:latest \
  --region asia-east1 \
  --platform managed \
  --allow-unauthenticated \
  --port 8080 \
  --memory 1Gi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 10 \
  --min-instances 0 \
  --concurrency 80 \
  --update-secrets GEMINI_API_KEY=GEMINI_API_KEY:latest,API_BEARER_TOKEN=API_BEARER_TOKEN:latest,GOOGLE_SEARCH_KEY=GOOGLE_SEARCH_KEY:latest,GOOGLE_SEARCH_ENGINE_ID=GOOGLE_SEARCH_ENGINE_ID:latest \
  --update-env-vars "GEMINI_MODEL=gemini-2.5-flash-lite,ALLOWED_ORIGINS=" \
  --cpu-boost
```

**Using Environment Variables (for testing only):**

```bash
gcloud run deploy agent-will-smith \
  --image asia-east1-docker.pkg.dev/uat-env-888888/docker-repo/agent-will-smith:latest \
  --region asia-east1 \
  --platform managed \
  --allow-unauthenticated \
  --port 8080 \
  --memory 1Gi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 10 \
  --min-instances 0 \
  --concurrency 80 \
  --set-env-vars "GEMINI_API_KEY=your-key-here,API_BEARER_TOKEN=your-token-here,GEMINI_MODEL=gemini-2.5-flash-lite,ALLOWED_ORIGINS=" \
  --cpu-boost
```

## Environment Variables

### Required Variables

- `GEMINI_API_KEY`: Your Google Gemini API key
- `API_BEARER_TOKEN`: Bearer token for API authentication
- `ALLOWED_ORIGINS`: Comma-separated list of allowed CORS origins

### Optional Variables

- `GEMINI_MODEL`: Model name (default: `gemini-2.5-flash-lite`)
- `LOG_LEVEL`: Logging level (default: `INFO`)
- `GOOGLE_SEARCH_KEY`: Google Custom Search API key (optional)
- `GOOGLE_SEARCH_ENGINE_ID`: Google Custom Search Engine ID (optional)

## Using Secret Manager (Recommended for Production)

Your previous deployment uses Secret Manager. The secrets should already exist with these names:
- `GEMINI_API_KEY`
- `API_BEARER_TOKEN`
- `GOOGLE_SEARCH_KEY`
- `GOOGLE_SEARCH_ENGINE_ID`

### 1. Verify Secrets Exist

```bash
gcloud secrets list --filter="name:(GEMINI_API_KEY OR API_BEARER_TOKEN OR GOOGLE_SEARCH_KEY OR GOOGLE_SEARCH_ENGINE_ID)"
```

### 2. Create/Update Secrets (if needed)

```bash
# Create or update Gemini API key secret
echo -n "your-gemini-api-key" | gcloud secrets create GEMINI_API_KEY \
  --data-file=- \
  --replication-policy="automatic" || \
echo -n "your-gemini-api-key" | gcloud secrets versions add GEMINI_API_KEY --data-file=-

# Create or update API bearer token secret
echo -n "your-bearer-token" | gcloud secrets create API_BEARER_TOKEN \
  --data-file=- \
  --replication-policy="automatic" || \
echo -n "your-bearer-token" | gcloud secrets versions add API_BEARER_TOKEN --data-file=-

# Create or update Google Search key (optional)
echo -n "your-search-key" | gcloud secrets create GOOGLE_SEARCH_KEY \
  --data-file=- \
  --replication-policy="automatic" || \
echo -n "your-search-key" | gcloud secrets versions add GOOGLE_SEARCH_KEY --data-file=-

# Create or update Google Search Engine ID (optional)
echo -n "your-search-engine-id" | gcloud secrets create GOOGLE_SEARCH_ENGINE_ID \
  --data-file=- \
  --replication-policy="automatic" || \
echo -n "your-search-engine-id" | gcloud secrets versions add GOOGLE_SEARCH_ENGINE_ID --data-file=-
```

### 3. Grant Cloud Run Access to Secrets

```bash
# Service account (matching your previous deployment)
SERVICE_ACCOUNT="731510304416-compute@developer.gserviceaccount.com"

# Grant secret accessor role for all secrets
for secret in GEMINI_API_KEY API_BEARER_TOKEN GOOGLE_SEARCH_KEY GOOGLE_SEARCH_ENGINE_ID; do
  gcloud secrets add-iam-policy-binding ${secret} \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/secretmanager.secretAccessor"
done
```

### 4. Deploy with Secrets

```bash
gcloud run deploy agent-will-smith \
  --image asia-east1-docker.pkg.dev/uat-env-888888/docker-repo/agent-will-smith:latest \
  --region asia-east1 \
  --platform managed \
  --allow-unauthenticated \
  --port 8080 \
  --memory 1Gi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 10 \
  --min-instances 0 \
  --concurrency 80 \
  --update-secrets GEMINI_API_KEY=GEMINI_API_KEY:latest,API_BEARER_TOKEN=API_BEARER_TOKEN:latest,GOOGLE_SEARCH_KEY=GOOGLE_SEARCH_KEY:latest,GOOGLE_SEARCH_ENGINE_ID=GOOGLE_SEARCH_ENGINE_ID:latest \
  --update-env-vars "GEMINI_MODEL=gemini-2.5-flash-lite,ALLOWED_ORIGINS=" \
  --cpu-boost
```

## Updating the Deployment

### Update Image and Redeploy

```bash
# Build new version (for linux/amd64 platform)
docker build --platform linux/amd64 -t asia-east1-docker.pkg.dev/uat-env-888888/docker-repo/agent-will-smith:latest .

# Push new version
docker push asia-east1-docker.pkg.dev/uat-env-888888/docker-repo/agent-will-smith:latest

# Deploy (Cloud Run will automatically use the latest image)
# Note: This preserves existing secrets and configuration
gcloud run deploy agent-will-smith \
  --image asia-east1-docker.pkg.dev/uat-env-888888/docker-repo/agent-will-smith:latest \
  --region asia-east1
```

Or use the deployment script:
```bash
./deploy-cloudrun.sh
```

Or use the deployment script:
```bash
./deploy-cloudrun.sh
```

## Configuration Options

### Resource Limits

Current configuration (matching previous deployment):
- **Port**: 8080 (Cloud Run standard)
- **Memory**: 1Gi
- **CPU**: 1
- **Timeout**: 300 seconds
- **Max Instances**: 10
- **Min Instances**: 0 (scales to zero)
- **Container Concurrency**: 80
- **CPU Boost**: Enabled (for faster cold starts)

Adjust based on your workload:

```bash
--memory 2Gi \        # Increase for larger workloads
--cpu 2 \             # Increase for CPU-intensive tasks
--timeout 600 \       # Increase timeout for long-running requests
--max-instances 20 \  # Scale up for high traffic
--min-instances 1 \   # Keep warm instances to reduce cold starts
--concurrency 100 \  # Increase concurrent requests per instance
```

### VPC Connector (if needed)

If your service needs to access resources in a VPC:

```bash
--vpc-connector your-vpc-connector \
--vpc-egress all-traffic
```

## Monitoring and Logs

### View Logs

```bash
gcloud run services logs read agent-will-smith --region asia-east1
```

### View Service Details

```bash
gcloud run services describe agent-will-smith --region asia-east1
```

### Get Service URL

```bash
gcloud run services describe agent-will-smith --region asia-east1 --format 'value(status.url)'
```

## Health Check

The service includes a health check endpoint:

```bash
curl https://your-service-url.run.app/health
```

## Troubleshooting

### Build Issues

- Ensure Docker is running
- Check that `.dockerignore` is properly configured
- Verify all dependencies are in `pyproject.toml`

### Deployment Issues

- Verify GCP project permissions
- Check Artifact Registry repository exists
- Ensure service account has necessary permissions

### Runtime Issues

- Check Cloud Run logs for errors
- Verify environment variables are set correctly
- Ensure secrets are accessible if using Secret Manager

## CI/CD Integration

For automated deployments, you can integrate this into your CI/CD pipeline:

```yaml
# Example GitHub Actions workflow
- name: Build and Push
  run: |
    docker build --platform linux/amd64 -t asia-east1-docker.pkg.dev/uat-env-888888/docker-repo/agent-will-smith:${{ github.sha }} .
    docker push asia-east1-docker.pkg.dev/uat-env-888888/docker-repo/agent-will-smith:${{ github.sha }}

- name: Deploy to Cloud Run
  run: |
    gcloud run deploy agent-will-smith \
      --image asia-east1-docker.pkg.dev/uat-env-888888/docker-repo/agent-will-smith:${{ github.sha }} \
      --region asia-east1
```

## Cost Optimization

- Use `--min-instances 0` to scale to zero when not in use
- Adjust `--max-instances` based on actual traffic
- Monitor usage in Cloud Console
- Consider using Cloud Run's CPU throttling for cost savings

