#!/usr/bin/env bash
# exit on error
set -e

echo ">>> Installing Python Backend Dependencies..."
pip install -r requirements.txt

echo ">>> Building React Frontend..."
cd founder_bi_agent/frontend

# Render natively includes recent Node versions alongside Python
npm install
npm run build

echo ">>> Build Complete!"
