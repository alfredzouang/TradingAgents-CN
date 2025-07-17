#!/bin/bash
# Build, push Docker image, create env ConfigMap from .env, and deploy TradingAgents-CN Helm chart to Kubernetes

set -e

# Defaults
CHART_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../helm" && pwd)"
RELEASE_NAME="tradingagents-cn"
NAMESPACE="default"
VALUES_FILE="$CHART_DIR/values.yaml"
DOCKERFILE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/Dockerfile"
IMAGE_REPO="tradingaz.azurecr.io"
IMAGE_NAME="tradingagents-cn"
if git rev-parse --is-inside-work-tree > /dev/null 2>&1; then
  IMAGE_TAG="$(git rev-parse --short HEAD)"
else
  IMAGE_TAG="$(date +%Y%m%d%H%M%S)"
fi
REGISTRY_URL="tradingaz.azurecr.io"
REGISTRY_USER="tradingaz"
REGISTRY_PASS="IGoooD70+5ldGAVQWL5LjRwW7XQP/zZviZqNSURO2i+ACRBzgkrD"
ENV_FILE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/.env"

usage() {
  echo "Usage: $0 [options]"
  echo "  -r|--repo <image_repo>         Container image repository (default: docker.io/<user>/tradingagents-cn)"
  echo "  -t|--tag <image_tag>           Image tag (default: current timestamp)"
  echo "  -u|--username <username>       Registry username (for authentication)"
  echo "  -p|--password <password>       Registry password or token"
  echo "  -n|--namespace <namespace>     Kubernetes namespace (default: default)"
  echo "  -f|--values <values.yaml>      Helm values file (default: helm/values.yaml)"
  echo "  -h|--help                      Show this help message"
  exit 1
}

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    -r|--repo)
      IMAGE_REPO="$2"
      shift 2
      ;;
    -t|--tag)
      IMAGE_TAG="$2"
      shift 2
      ;;
    -u|--username)
      REGISTRY_USER="$2"
      shift 2
      ;;
    -p|--password)
      REGISTRY_PASS="$2"
      shift 2
      ;;
    -n|--namespace)
      NAMESPACE="$2"
      shift 2
      ;;
    -f|--values)
      VALUES_FILE="$2"
      shift 2
      ;;
    -h|--help)
      usage
      ;;
    *)
      echo "Unknown argument: $1"
      usage
      ;;
  esac
done

# Determine Docker image full name
if [[ "$IMAGE_REPO" == "docker.io" ]]; then
  if [[ -z "$REGISTRY_USER" || -z "$REGISTRY_PASS" ]]; then
    echo "For Docker Hub, please provide both username (-u) and password/token (-p) for non-interactive login."
    exit 1
  fi
  FULL_IMAGE_NAME="docker.io/$REGISTRY_USER/$IMAGE_NAME:$IMAGE_TAG"
  REGISTRY_URL="docker.io"
else
  FULL_IMAGE_NAME="$IMAGE_REPO/$IMAGE_NAME:$IMAGE_TAG"
  REGISTRY_URL="$IMAGE_REPO"
fi

# Check if image with tag exists in registry
IMAGE_EXISTS=false
if [[ "$IMAGE_REPO" == "tradingaz.azurecr.io" ]]; then
  if command -v az >/dev/null 2>&1; then
    EXISTING_TAGS=$(az acr repository show-tags --name tradingaz --repository "$IMAGE_NAME" --output tsv 2>/dev/null || true)
    for tag in $EXISTING_TAGS; do
      if [[ "$tag" == "$IMAGE_TAG" ]]; then
        IMAGE_EXISTS=true
        break
      fi
    done
  fi
elif [[ "$IMAGE_REPO" == "docker.io" ]]; then
  # Docker Hub check (public images only)
  REPO_PATH="$REGISTRY_USER/$IMAGE_NAME"
  HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "https://hub.docker.com/v2/repositories/$REPO_PATH/tags/$IMAGE_TAG/")
  if [[ "$HTTP_STATUS" == "200" ]]; then
    IMAGE_EXISTS=true
  fi
fi

if [[ "$IMAGE_EXISTS" == "true" ]]; then
  echo "Image $FULL_IMAGE_NAME already exists in registry, skipping build and push."
else
  echo "Building Docker image: $FULL_IMAGE_NAME"
  PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
  docker build --platform=linux/amd64 -t "$FULL_IMAGE_NAME" -f "$DOCKERFILE" "$PROJECT_ROOT"

  if [[ -n "$REGISTRY_USER" && -n "$REGISTRY_PASS" ]]; then
    echo "Logging in to registry $REGISTRY_URL"
    echo "$REGISTRY_PASS" | docker login "$REGISTRY_URL" -u "$REGISTRY_USER" --password-stdin
  fi

  echo "Pushing Docker image: $FULL_IMAGE_NAME"
  docker push "$FULL_IMAGE_NAME"

  echo "Image pushed: $FULL_IMAGE_NAME"
fi

# Create env ConfigMap from .env (excluding sensitive keys)
CONFIGMAP_NAME="${RELEASE_NAME}-env"
SENSITIVE_KEYS=(
  DASHSCOPE_API_KEY
  FINNHUB_API_KEY
  TUSHARE_TOKEN
  OPENAI_API_KEY
  GOOGLE_API_KEY
  ANTHROPIC_API_KEY
  DEEPSEEK_API_KEY
  AZURE_OPENAI_API_KEY
  MONGODB_PASSWORD
  REDIS_PASSWORD
  REDDIT_CLIENT_SECRET
)

echo "Creating/updating ConfigMap $CONFIGMAP_NAME from $ENV_FILE (excluding sensitive keys)..."
CONFIGMAP_LITERALS=()
while IFS='=' read -r key value; do
  # Skip comments and empty lines
  [[ "$key" =~ ^#.*$ || -z "$key" ]] && continue
  # Remove export if present
  key="${key#export }"
  # Remove quotes around value
  value="${value%\"}"
  value="${value#\"}"
  # Skip sensitive keys
  skip=false
  for s in "${SENSITIVE_KEYS[@]}"; do
    if [[ "$key" == "$s" ]]; then
      skip=true
      break
    fi
  done
  $skip && continue
  CONFIGMAP_LITERALS+=(--from-literal="$key=$value")
done < "$ENV_FILE"

if [[ ${#CONFIGMAP_LITERALS[@]} -eq 0 ]]; then
  echo "No non-sensitive envs found in $ENV_FILE"
else
  kubectl create configmap "$CONFIGMAP_NAME" -n "$NAMESPACE" "${CONFIGMAP_LITERALS[@]}" --dry-run=client -o yaml | kubectl apply -f -
  echo "ConfigMap $CONFIGMAP_NAME created/updated."
fi

# Deploy with Helm, passing image repo/tag
echo "Deploying $RELEASE_NAME to namespace $NAMESPACE using values file $VALUES_FILE"
helm upgrade --install "$RELEASE_NAME" "$CHART_DIR" \
  -n "$NAMESPACE" \
  -f "$VALUES_FILE" \
  --set web.image="${IMAGE_REPO}/${IMAGE_NAME}" \
  --set web.tag="${IMAGE_TAG}" \
  --create-namespace

echo "Deployment complete."
echo "Deployed image: $FULL_IMAGE_NAME"
