#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="/opt/nutriflow-ai"
PUBLIC_DIR="/var/www/nutriflow-ai"
VENV_DIR="$PROJECT_DIR/.venv"
SERVICE_NAME="nutriflow-backend"

echo "==> NutriFlow deploy started"
cd "$PROJECT_DIR"

echo "==> Updating code"
git pull --ff-only

echo "==> Ensuring Python virtualenv"
if [ ! -d "$VENV_DIR" ]; then
  python3 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"

echo "==> Installing backend dependencies"
python -m pip install --upgrade pip
python -m pip install -r backend/requirements.txt
python -m pip install -r backend/requirements-dev.txt

echo "==> Running database migrations"
alembic upgrade head

echo "==> Installing frontend dependencies"
cd "$PROJECT_DIR/frontend"
if [ -f package-lock.json ]; then
  npm ci
else
  npm install
fi

echo "==> Building frontend"
npm run build

echo "==> Publishing frontend"
mkdir -p "$PUBLIC_DIR"
rsync -av --delete dist/ "$PUBLIC_DIR/"
chown -R www-data:www-data "$PUBLIC_DIR"

echo "==> Restarting backend service"
systemctl restart "$SERVICE_NAME"

echo "==> Waiting for backend to become ready"
for i in $(seq 1 20); do
  if curl -fsS http://127.0.0.1:8010/health >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

echo "==> Validating nginx"
nginx -t

echo "==> Reloading nginx"
systemctl reload nginx

echo "==> Smoke tests"
curl -fsS http://127.0.0.1:8010/health
curl -fsS -H "Host: nutriflow.lptd.casa" http://127.0.0.1 >/dev/null
curl -fsS -H "Host: nutriflow.lptd.casa" http://127.0.0.1/api/health >/dev/null

echo "==> Deploy finished successfully"
