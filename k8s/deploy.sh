#!/bin/bash
# =============================================================================
# ShopNow — Minikube Deployment Script (with Infisical secret management)
# =============================================================================
# Usage:
#   ./deploy.sh           — full deploy (first time)
#   ./deploy.sh teardown  — destroy everything
#   ./deploy.sh status    — show all resource status
#   ./deploy.sh logs api  — tail logs for a component
#   ./deploy.sh refresh   — re-sync secrets from Infisical
# =============================================================================

set -e

NAMESPACE="ecommerce"
DOCKERHUB_USERNAME="${DOCKERHUB_USERNAME:-johnitopaisah}"
INFISICAL_OPERATOR_VERSION="0.8.1"

# ── Colours ───────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; BOLD='\033[1m'; NC='\033[0m'

info()    { echo -e "${BLUE}[INFO]${NC}  $*"; }
success() { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }
step()    { echo -e "\n${BOLD}══ $* ══${NC}"; }

# =============================================================================
# TEARDOWN
# =============================================================================
if [[ "$1" == "teardown" ]]; then
  warn "Deleting all ShopNow resources from minikube..."
  kubectl delete namespace $NAMESPACE --ignore-not-found
  warn "Removing Infisical operator..."
  helm uninstall infisical-operator -n infisical-operator --ignore-not-found 2>/dev/null || true
  kubectl delete namespace infisical-operator --ignore-not-found
  success "All resources removed."
  exit 0
fi

# =============================================================================
# STATUS
# =============================================================================
if [[ "$1" == "status" ]]; then
  echo -e "\n${BOLD}Pods:${NC}"
  kubectl get pods -n $NAMESPACE -o wide
  echo -e "\n${BOLD}Services:${NC}"
  kubectl get svc -n $NAMESPACE
  echo -e "\n${BOLD}Deployments:${NC}"
  kubectl get deployments -n $NAMESPACE
  echo -e "\n${BOLD}StatefulSets:${NC}"
  kubectl get statefulsets -n $NAMESPACE
  echo -e "\n${BOLD}Ingress:${NC}"
  kubectl get ingress -n $NAMESPACE
  echo -e "\n${BOLD}PersistentVolumeClaims:${NC}"
  kubectl get pvc -n $NAMESPACE
  echo -e "\n${BOLD}InfisicalSecrets:${NC}"
  kubectl get infisicalsecret -n $NAMESPACE 2>/dev/null || echo "  (Infisical CRD not installed)"
  echo -e "\n${BOLD}Infisical Operator:${NC}"
  kubectl get pods -n infisical-operator 2>/dev/null || echo "  (not installed)"
  exit 0
fi

# =============================================================================
# LOGS
# =============================================================================
if [[ "$1" == "logs" ]]; then
  COMPONENT="${2:-api}"
  kubectl logs -n $NAMESPACE -l "component=$COMPONENT" --tail=100 -f
  exit 0
fi

# =============================================================================
# SECRET REFRESH (force re-sync)
# =============================================================================
if [[ "$1" == "refresh" ]]; then
  info "Forcing Infisical secret re-sync..."
  kubectl annotate infisicalsecret shopnow-secrets \
    -n $NAMESPACE \
    "infisical.com/force-sync=$(date +%s)" \
    --overwrite
  success "Re-sync triggered. Secrets will update within 60 seconds."
  info "Watch: kubectl get secret api-secret -n $NAMESPACE"
  exit 0
fi

# =============================================================================
# FULL DEPLOY
# =============================================================================

step "0. Pre-flight checks"

minikube status > /dev/null 2>&1 || error "Minikube not running. Run: minikube start"
success "Minikube running"

if ! minikube addons list | grep -q "ingress.*enabled"; then
  warn "Enabling ingress addon..."
  minikube addons enable ingress
  sleep 30
fi
success "Ingress addon enabled"

CONTEXT=$(kubectl config current-context)
[[ "$CONTEXT" != "minikube" ]] && error "kubectl context is '$CONTEXT', not 'minikube'"
success "kubectl context: minikube"

command -v helm > /dev/null 2>&1 || error "Helm not found. Install: https://helm.sh/docs/intro/install/"
success "Helm found: $(helm version --short)"

# =============================================================================
step "1. Create namespace"
kubectl apply -f k8s/namespace.yaml
success "Namespace '$NAMESPACE' ready"

# =============================================================================
step "2. Install Infisical Operator (secret manager agent)"

# Create operator namespace
kubectl create namespace infisical-operator --dry-run=client -o yaml | kubectl apply -f -

# Add Infisical Helm repo
helm repo add infisical-helm-charts \
  https://dl.cloudsmith.io/public/infisical/helm-charts/helm/charts/ \
  --force-update 2>/dev/null || true
helm repo update

# Install or upgrade the operator
if helm status infisical-operator -n infisical-operator > /dev/null 2>&1; then
  info "Infisical operator already installed — upgrading..."
  helm upgrade infisical-operator infisical-helm-charts/secrets-operator \
    -n infisical-operator \
    --version "$INFISICAL_OPERATOR_VERSION" \
    --wait --timeout=120s
else
  helm install infisical-operator infisical-helm-charts/secrets-operator \
    -n infisical-operator \
    --version "$INFISICAL_OPERATOR_VERSION" \
    --wait --timeout=120s
fi

info "Waiting for operator pod to be ready..."
kubectl rollout status deployment \
  -n infisical-operator \
  --timeout=90s \
  $(kubectl get deployment -n infisical-operator -o name 2>/dev/null | head -1) \
  2>/dev/null || warn "Operator rollout check skipped"

success "Infisical operator installed"

# =============================================================================
step "3. Configure Infisical authentication"

# Check the auth secret has been filled in
CLIENT_ID=$(kubectl get secret infisical-machine-identity \
  -n $NAMESPACE \
  -o jsonpath='{.data.clientId}' 2>/dev/null || echo "")

if [[ -z "$CLIENT_ID" || "$CLIENT_ID" == "REPLACE_WITH_BASE64_CLIENT_ID" ]]; then
  warn "Infisical machine identity not configured yet."
  echo ""
  echo -e "  1. Go to ${BOLD}https://app.infisical.com${NC}"
  echo -e "  2. Project Settings → Machine Identities → k8s-operator"
  echo -e "  3. Copy the Client ID and Client Secret"
  echo -e "  4. Run:"
  echo ""
  echo -e "     kubectl create secret generic infisical-machine-identity \\"
  echo -e "       --from-literal=clientId=YOUR_CLIENT_ID \\"
  echo -e "       --from-literal=clientSecret=YOUR_CLIENT_SECRET \\"
  echo -e "       -n $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -"
  echo ""
  echo -e "  5. Then re-run: ${BOLD}./k8s/deploy.sh${NC}"
  echo ""
  error "Infisical credentials missing — deployment stopped."
fi

success "Infisical machine identity secret found"

# =============================================================================
step "4. Apply InfisicalSecret sync definition"

# Check projectSlug has been updated
if grep -q "REPLACE_WITH_YOUR_PROJECT_SLUG" k8s/infisical/infisical-secret.yaml; then
  warn "InfisicalSecret has placeholder projectSlug."
  echo ""
  echo -e "  1. Go to ${BOLD}https://app.infisical.com${NC} → your project"
  echo -e "  2. Settings → Project ID (copy the slug)"
  echo -e "  3. Edit ${BOLD}k8s/infisical/infisical-secret.yaml${NC}"
  echo -e "     Replace ${BOLD}REPLACE_WITH_YOUR_PROJECT_SLUG${NC} with your actual slug"
  echo ""
  error "projectSlug not configured — deployment stopped."
fi

kubectl apply -f k8s/infisical/infisical-secret.yaml

info "Waiting for Infisical to sync secrets (up to 60s)..."
for i in $(seq 1 12); do
  if kubectl get secret api-secret -n $NAMESPACE > /dev/null 2>&1; then
    success "Infisical synced 'api-secret' to Kubernetes"
    break
  fi
  echo -n "."
  sleep 5
done

kubectl get secret api-secret -n $NAMESPACE > /dev/null 2>&1 \
  || error "api-secret was not created by Infisical. Check operator logs:
    kubectl logs -n infisical-operator \$(kubectl get pod -n infisical-operator -o name | head -1)"

# =============================================================================
step "5. Create Docker Hub image pull secret"

if kubectl get secret dockerhub-secret -n $NAMESPACE > /dev/null 2>&1; then
  warn "dockerhub-secret already exists — skipping"
else
  if [[ -z "$DOCKERHUB_PASSWORD" ]]; then
    echo -n "Enter Docker Hub access token: "
    read -s DOCKERHUB_PASSWORD; echo
  fi
  if [[ -z "$DOCKERHUB_EMAIL" ]]; then
    echo -n "Enter Docker Hub email: "
    read DOCKERHUB_EMAIL
  fi
  kubectl create secret docker-registry dockerhub-secret \
    --docker-server=https://index.docker.io/v1/ \
    --docker-username="$DOCKERHUB_USERNAME" \
    --docker-password="$DOCKERHUB_PASSWORD" \
    --docker-email="$DOCKERHUB_EMAIL" \
    --namespace=$NAMESPACE
  success "dockerhub-secret created"
fi

# =============================================================================
step "6. Apply ConfigMap (non-sensitive config)"
kubectl apply -f k8s/configmaps/api-config.yaml
success "ConfigMap applied"

# =============================================================================
step "7. Deploy PostgreSQL"
kubectl apply -f k8s/postgres/statefulset.yaml
kubectl apply -f k8s/postgres/service.yaml
info "Waiting for PostgreSQL..."
kubectl rollout status statefulset/postgres -n $NAMESPACE --timeout=120s
success "PostgreSQL ready"

# =============================================================================
step "8. Deploy Redis"
kubectl apply -f k8s/redis/statefulset.yaml
kubectl apply -f k8s/redis/service.yaml
info "Waiting for Redis..."
kubectl rollout status statefulset/redis -n $NAMESPACE --timeout=60s
success "Redis ready"

# =============================================================================
step "9. Run database migrations"
kubectl delete job api-migrate -n $NAMESPACE --ignore-not-found
kubectl apply -f k8s/api/migrate-job.yaml
info "Waiting for migrations (up to 3 minutes)..."
kubectl wait --for=condition=complete job/api-migrate \
  -n $NAMESPACE --timeout=180s \
  && success "Migrations completed" \
  || error "Migration failed. Logs: kubectl logs -n $NAMESPACE job/api-migrate"

# =============================================================================
step "10. Deploy API"
kubectl apply -f k8s/api/deployment.yaml
kubectl apply -f k8s/api/service.yaml
kubectl rollout status deployment/api -n $NAMESPACE --timeout=180s
success "API deployed"

# =============================================================================
step "11. Deploy User UI"
kubectl apply -f k8s/user-ui/deployment.yaml
kubectl apply -f k8s/user-ui/service.yaml
kubectl rollout status deployment/user-ui -n $NAMESPACE --timeout=120s
success "User UI deployed"

# =============================================================================
step "12. Deploy Admin UI"
kubectl apply -f k8s/admin-ui/deployment.yaml
kubectl apply -f k8s/admin-ui/service.yaml
kubectl rollout status deployment/admin-ui -n $NAMESPACE --timeout=120s
success "Admin UI deployed"

# =============================================================================
step "13. Apply Ingress"
kubectl apply -f k8s/ingress/ingress.yaml
success "Ingress applied"

# =============================================================================
step "14. Configure /etc/hosts"
MINIKUBE_IP=$(minikube ip)
HOSTS_ENTRY="$MINIKUBE_IP shopnow.local"

if grep -q "shopnow.local" /etc/hosts; then
  warn "/etc/hosts already has shopnow.local — skipping"
else
  echo "$HOSTS_ENTRY" | sudo tee -a /etc/hosts > /dev/null
  success "Added $HOSTS_ENTRY to /etc/hosts"
fi

# =============================================================================
step "15. Seed the database"
kubectl wait --for=condition=ready pod \
  -l "component=api" -n $NAMESPACE --timeout=120s

API_POD=$(kubectl get pod -n $NAMESPACE -l component=api \
  -o jsonpath='{.items[0].metadata.name}')
kubectl exec -n $NAMESPACE "$API_POD" -- \
  python manage.py seed_db && success "Database seeded" \
  || warn "Seed skipped (already seeded or failed — check manually)"

# =============================================================================
step "Deployment complete!"

echo ""
echo -e "${GREEN}${BOLD}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}${BOLD}║         ShopNow is running on minikube                ║${NC}"
echo -e "${GREEN}${BOLD}║         Secrets managed by Infisical ✓                ║${NC}"
echo -e "${GREEN}${BOLD}╚══════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  ${BOLD}Storefront:${NC}    http://shopnow.local"
echo -e "  ${BOLD}Admin panel:${NC}   http://shopnow.local/admin-panel/"
echo -e "  ${BOLD}API:${NC}           http://shopnow.local/api/v1/"
echo -e "  ${BOLD}Swagger:${NC}       http://shopnow.local/api/docs/"
echo ""
echo -e "  ${BOLD}Admin login:${NC}   admin@test.com / Admin1234!"
echo ""
echo -e "  ${BOLD}Secret management:${NC}"
echo -e "    Update a secret  → change in Infisical dashboard"
echo -e "    Auto-sync        → every 60 seconds"
echo -e "    Force sync now   → ./k8s/deploy.sh refresh"
echo ""
echo -e "  ${BOLD}Useful commands:${NC}"
echo -e "    ./k8s/deploy.sh status      — all pod/service status"
echo -e "    ./k8s/deploy.sh logs api    — tail API logs"
echo -e "    ./k8s/deploy.sh teardown    — remove everything"
echo -e "    minikube dashboard          — visual dashboard"
echo ""
