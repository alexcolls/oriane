#!/usr/bin/env bash
set -euo pipefail

SSH_KEY="keys/qdrant-dev-key.pem"
HOST="ubuntu@ec2-44-222-164-61.compute-1.amazonaws.com"

chmod 600 "$SSH_KEY"

echo "📤 Copying remote-setup.sh to remote host..."
scp -i "$SSH_KEY" remote-setup.sh "$HOST:/tmp/remote-setup.sh"

echo "📤 Copying docker-compose.yml, .env, and nginx.conf to remote host..."
scp -i "$SSH_KEY" docker-compose.yml .env nginx.conf "$HOST:/opt/qdrant-stack/"

echo "✅ Files transferred"

echo "🚀 Running remote setup..."
ssh -i "$SSH_KEY" "$HOST" 'bash /tmp/remote-setup.sh'
