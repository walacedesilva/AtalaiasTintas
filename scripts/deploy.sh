#!/bin/bash
# v2 - runner reiniciado para fix de permissoes
# =============================================================================
# Script de Auto-Deploy - Atalaia Tintas
# Executado pelo GitHub Actions runner ao push na branch Develop
# =============================================================================
set -e

PROJECT_DIR="/root/AtalaiasTintas"
FRONTEND_DIST="/var/www/atalaiastintas"
LOG_FILE="/tmp/atalaias-deploy.log"
COMPOSE_FILE="deployment/docker/docker-compose.prod.yml"
ENV_FILE=".env.prod"

# Node 20 instalado em /usr/local/bin
export PATH=/usr/local/bin:$PATH
export DOCKER_BUILDKIT=1

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "========================================="
log "Iniciando deploy - branch: $(git -C $PROJECT_DIR branch --show-current)"
log "Commit: $(git -C $PROJECT_DIR log -1 --oneline)"
log "========================================="

cd "$PROJECT_DIR"

# 1. Baixar últimas alterações
log ">> Atualizando código..."
GIT_TERMINAL_PROMPT=0 GIT_HTTP_LOW_SPEED_LIMIT=1000 GIT_HTTP_LOW_SPEED_TIME=30 \
    timeout 120 git pull origin Develop

# 2. Rebuild das imagens Docker (apenas se mudou o backend)
if git diff HEAD@{1} HEAD --name-only | grep -qE "^backend/|^requirements/|^deployment/docker/Dockerfile"; then
    log ">> Alterações no backend detectadas. Rebuild das imagens..."
    sudo -E docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" build web worker
    log ">> Restart dos containers..."
    sudo -E docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d web worker
    # Aguardar subir
    sleep 20
    sudo docker logs atalaias_web 2>&1 | grep -E "Listening|ERROR" | tail -5 | tee -a "$LOG_FILE"
    # Rodar migrations
    log ">> Rodando migrations..."
    sudo docker exec atalaias_web bash -c "cd backend && python manage.py migrate --no-input" | tee -a "$LOG_FILE"
else
    log ">> Sem alterações no backend. Pulando rebuild das imagens."
    # Restart leve para pegar mudanças de código (volume bind)
    sudo -E docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" restart web worker
fi

# 3. Rebuild do frontend (apenas se mudou)
if git diff HEAD@{1} HEAD --name-only | grep -qE "^frontend/"; then
    log ">> Alterações no frontend detectadas. Rebuilding React..."
    export PATH=/usr/local/bin:$PATH
    cd "$PROJECT_DIR/frontend"
    npm ci
    npm run build
    sudo cp -r dist/. "$FRONTEND_DIST/"
    sudo chown -R www-data:www-data "$FRONTEND_DIST"
    cd "$PROJECT_DIR"
    log ">> Frontend atualizado em $FRONTEND_DIST"
else
    log ">> Sem alterações no frontend. Pulando rebuild."
fi

log ">> Deploy concluído com sucesso!"
log "========================================="
