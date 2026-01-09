.PHONY: help docker-login docker-build docker-tag docker-push docker-push-all clean

# Variables
AWS_REGION := ap-northeast-1
AWS_PROFILE := c2g-uat
ECR_REGISTRY := 147997115496.dkr.ecr.$(AWS_REGION).amazonaws.com
ECR_REPO := aigc/agent-will-smith
IMAGE_NAME := agent-will-smith
VERSION := v0.1.2

# Full ECR URL
ECR_URL := $(ECR_REGISTRY)/$(ECR_REPO)

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'

docker-login: ## Login to AWS ECR
	@echo "Setting AWS profile to $(AWS_PROFILE)..."
	@export AWS_PROFILE=$(AWS_PROFILE) && \
	aws ecr get-login-password --region $(AWS_REGION) | \
	docker login --username AWS --password-stdin $(ECR_REGISTRY)

docker-build: ## Build Docker image
	@echo "Building $(IMAGE_NAME):$(VERSION)..."
	docker build -t $(IMAGE_NAME):$(VERSION) .

docker-tag: ## Tag Docker image for ECR
	@echo "Tagging $(IMAGE_NAME):$(VERSION) for ECR..."
	docker tag $(IMAGE_NAME):$(VERSION) $(ECR_URL):$(VERSION)
	docker tag $(IMAGE_NAME):$(VERSION) $(ECR_URL):latest

docker-push: ## Push Docker images to ECR
	@echo "Pushing $(ECR_URL):$(VERSION)..."
	docker push $(ECR_URL):$(VERSION)
	@echo "Pushing $(ECR_URL):latest..."
	docker push $(ECR_URL):latest

docker-push-all: docker-login docker-build docker-tag docker-push ## Build and push Docker image to ECR (all steps)
	@echo "✅ Successfully pushed $(IMAGE_NAME):$(VERSION) and latest to ECR!"
	@echo "Image URL: $(ECR_URL):$(VERSION)"

docker-run-local: ## Run Docker image locally
	docker run -p 8000:8000 --env-file .env $(IMAGE_NAME):$(VERSION)

clean: ## Remove local Docker images
	@echo "Removing local Docker images..."
	-docker rmi $(IMAGE_NAME):$(VERSION)
	-docker rmi $(ECR_URL):$(VERSION)
	-docker rmi $(ECR_URL):latest
	@echo "✅ Cleanup complete!"

