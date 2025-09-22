#!/bin/bash

# Setup script for Ollama models
# This script downloads and sets up the required models for Brebot

echo "🚀 Setting up Ollama models for Brebot..."

# Wait for Ollama to be ready
echo "⏳ Waiting for Ollama to be ready..."
until curl -f http://localhost:11434/api/tags > /dev/null 2>&1; do
    echo "Waiting for Ollama..."
    sleep 5
done

echo "✅ Ollama is ready!"

# Pull the main LLM model
echo "📥 Pulling Llama 3.1 8B model..."
ollama pull llama3.1:8b

# Pull the embedding model
echo "📥 Pulling Nomic Embed Text model..."
ollama pull nomic-embed-text

# Optional: Pull additional models
echo "📥 Pulling additional useful models..."
ollama pull codellama:7b  # For code-related tasks
ollama pull mistral:7b    # Alternative LLM

echo "✅ All models downloaded successfully!"
echo "🎉 Brebot is ready to use!"

# List available models
echo "📋 Available models:"
ollama list
