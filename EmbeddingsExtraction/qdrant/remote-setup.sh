#!/usr/bin/env bash
set -euo pipefail

STACK_DIR="/opt/qdrant-stack"
DATA_DIR="/qdrant_data"
REMOTE_USER=$(id -un)

echo "🔧 Installing Docker dependencies..."
sudo rm -f /etc/apt/sources.list.d/docker.list || true
sudo apt-get update -qq
sudo apt-get install -y ca-certificates curl gnupg lsb-release

echo "🔐 Adding Docker GPG key..."
sudo install -d -m 0755 /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  | sudo gpg --dearmor --batch --yes -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

arch=$(dpkg --print-architecture)
codename=$(lsb_release -cs)
echo "📦 Adding Docker APT repo..."
echo "deb [arch=${arch} signed-by=/etc/apt/keyrings/docker.gpg] \
https://download.docker.com/linux/ubuntu ${codename} stable" \
  | sudo tee /etc/apt/sources.list.d/docker.list >/dev/null

echo "📥 Installing Docker engine and compose plugin..."
sudo apt-get update -qq
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

echo "👤 Adding user '${REMOTE_USER}' to docker group..."
sudo usermod -aG docker "$REMOTE_USER"

echo "📁 Creating stack and data directories..."
sudo mkdir -p "$DATA_DIR" "$STACK_DIR"
sudo chown 100:100 "$DATA_DIR"
sudo chown "$REMOTE_USER:$REMOTE_USER" "$STACK_DIR"

echo "🌐 Installing Nginx and Certbot..."
sudo apt-get install -y nginx certbot python3-certbot-nginx

echo "🔐 Obtaining SSL certificate..."
sudo certbot --nginx \
    -d qdrant.admin.oriane.xyz \
    --agree-tos \
    --redirect \
    --hsts \
    --staple-ocsp \
    --email alex@oriane.xyz \
    --no-eff-email

if [[ -f "$STACK_DIR/nginx.conf" ]]; then
  echo "🔁 Linking nginx.conf to /etc/nginx/nginx.conf"
  sudo cp /etc/nginx/nginx.conf /etc/nginx/nginx.conf.bak || true
  sudo ln -sf "$STACK_DIR/nginx.conf" /etc/nginx/nginx.conf
else
  echo "⚠️ nginx.conf not found in $STACK_DIR, please copy it before restarting nginx"
fi

echo "📡 Enabling and starting Nginx..."
sudo systemctl enable nginx
sudo systemctl restart nginx

echo "✅ Remote setup complete"
