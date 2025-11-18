#!/bin/bash
# Setup script for Ollama with Qwen2.5-Coder model

set -e

echo "🚀 Setting up Ollama with Qwen2.5-Coder..."

# Start Ollama service
echo "📦 Starting Ollama service..."
docker-compose up -d ollama

# Wait for Ollama to be healthy
echo "⏳ Waiting for Ollama to be ready..."
timeout 60 bash -c 'until docker-compose exec ollama curl -sf http://localhost:11434/api/tags > /dev/null; do sleep 2; done' || {
    echo "❌ Ollama failed to start"
    exit 1
}

echo "✅ Ollama is running"

# Pull the model
echo "📥 Pulling qwen2.5-coder:3b model (this may take a few minutes)..."
docker-compose exec ollama ollama pull qwen2.5-coder:3b

# Verify the model
echo "🔍 Verifying model installation..."
docker-compose exec ollama ollama list

echo "✅ Ollama setup complete!"
echo ""
echo "You can test the model with:"
echo "  docker-compose exec ollama ollama run qwen2.5-coder:3b"
echo ""
echo "Or use it via the API:"
echo "  curl http://localhost:11434/api/generate -d '{\"model\":\"qwen2.5-coder:3b\",\"prompt\":\"Write a hello world in Python\",\"stream\":false}'"
