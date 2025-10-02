#!/usr/bin/env bash
# deploy-image.sh – from zero to running Qdrant on EC2 (no $USER pitfalls)
set -euo pipefail

SSH_KEY="keys/qdrant-dev-key.pem"                       # local .pem
HOST="ubuntu@ec2-44-222-164-61.compute-1.amazonaws.com" # change if needed

STACK_DIR="/opt/qdrant-stack"
DATA_DIR="/qdrant_data"

# ---------------------------------------------------------------------------
# sanity-check local files
# ---------------------------------------------------------------------------
[[ -f docker-compose.yml ]] || { echo "❌ docker-compose.yml missing"; exit 1; }
[[ -f .env ]]               || { echo "❌ .env missing"; exit 1; }
chmod 600 "$SSH_KEY"

# ---------------------------------------------------------------------------
# 1) bootstrap remote host (Docker repo, engine, dirs, ownership)
# ---------------------------------------------------------------------------
ssh -i "$SSH_KEY" "$HOST" 'bash -se' <<'REMOTE'
set -euo pipefail

STACK_DIR="/opt/qdrant-stack"
DATA_DIR="/qdrant_data"
REMOTE_USER=$(id -un)          # reliable user name inside SSH session

echo "🔧 Installing / verifying Docker …"
sudo rm -f /etc/apt/sources.list.d/docker.list || true
sudo apt-get update -qq
sudo apt-get install -y ca-certificates curl gnupg lsb-release

sudo install -d -m 0755 /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
 | sudo gpg --dearmor --batch --yes -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

arch=$(dpkg --print-architecture)
codename=$(lsb_release -cs)
echo "deb [arch=${arch} signed-by=/etc/apt/keyrings/docker.gpg] \
https://download.docker.com/linux/ubuntu ${codename} stable" \
 | sudo tee /etc/apt/sources.list.d/docker.list >/dev/null

sudo apt-get update -qq
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
sudo usermod -aG docker "$REMOTE_USER"     # safe: user definitely exists

# create directories with correct owners
sudo mkdir -p "$DATA_DIR" "$STACK_DIR"
sudo chown 100:100       "$DATA_DIR"       # container UID
sudo chown "$REMOTE_USER":"$REMOTE_USER" "$STACK_DIR"
REMOTE

# ---------------------------------------------------------------------------
# 2) copy compose + .env to remote stack dir
# ---------------------------------------------------------------------------
scp -i "$SSH_KEY" docker-compose.yml Caddyfile .env "$HOST:$STACK_DIR/"

# ---------------------------------------------------------------------------
# 3) systemd unit & (re)start stack
# ---------------------------------------------------------------------------
ssh -i "$SSH_KEY" "$HOST" 'bash -se' <<'REMOTE'
set -euo pipefail
SERVICE=/etc/systemd/system/qdrant-compose.service

if [[ ! -f $SERVICE ]]; then
sudo tee $SERVICE >/dev/null <<'UNIT'
[Unit]
Description=Qdrant via docker-compose
After=network.target docker.service
Requires=docker.service

[Service]
Type=oneshot
WorkingDirectory=/opt/qdrant-stack
ExecStartPre=/usr/bin/docker compose pull
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
UNIT
  sudo systemctl daemon-reload
  sudo systemctl enable qdrant-compose
fi

echo "🚀 Starting (or restarting) Qdrant …"
cd /opt/qdrant-stack
sudo docker compose up -d
REMOTE

# ---------------------------------------------------------------------------
# 4) wait until /healthz (>=1.12) or /ready (<1.12) responds
# ---------------------------------------------------------------------------
API_KEY=$(grep -m1 '^QDRANT_API_KEY=' .env | cut -d= -f2-)
printf "\n⏳ Waiting for Qdrant … "
ssh -i "$SSH_KEY" "$HOST" bash -se <<REMOTE
until curl -fs -H "api-key: $API_KEY" http://localhost:6333/healthz >/dev/null \
   || curl -fs -H "api-key: $API_KEY" http://localhost:6333/ready  >/dev/null; do
  sleep 2
done
REMOTE
echo "✅ ready"

echo -e "\nREST  → http://${HOST#*@}:6333"
echo   "gRPC → http://${HOST#*@}:6334   (api-key in .env)"
echo   "UI → http://${HOST#*@}:8080"
