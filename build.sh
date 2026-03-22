#!/usr/bin/env bash
# exit on error
set -e

echo ">>> LLM_PROVIDER detected: ${LLM_PROVIDER:-google}"

echo ">>> Installing Python Backend Dependencies..."
pip install -r requirements.txt

if [ "${LLM_PROVIDER}" == "google" ] || [ "${LLM_PROVIDER}" == "gemini" ]; then
  echo ">>> [CONFIG] Prioritizing Google Gemini libraries..."
  pip install --upgrade google-generativeai google-genai langchain-google-genai
elif [ "${LLM_PROVIDER}" == "huggingface" ] || [ "${LLM_PROVIDER}" == "groq" ]; then
  echo ">>> [CONFIG] Prioritizing OpenAI-compatible / HuggingFace libraries..."
  pip install --upgrade openai
fi

echo ">>> Building React Frontend..."
cd founder_bi_agent/frontend

# Install node dependencies
npm install

# Build the frontend assets
npm run build

# Robustness check: Ensure dist exists and contains index.html
if [ ! -f "dist/index.html" ]; then
    echo "ERROR: Frontend build failed to produce dist/index.html"
    exit 1
fi

echo ">>> Build Complete! Robustness checks passed."
