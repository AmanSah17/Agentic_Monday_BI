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

# Render natively includes recent Node versions alongside Python
npm install
npm run build

echo ">>> Build Complete!"
