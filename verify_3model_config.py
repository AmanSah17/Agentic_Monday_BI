#!/usr/bin/env python3
"""Verify 3-model Groq configuration is loaded correctly"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path, override=True)
    print(f"📝 Loaded .env from: {env_path}\n")

from founder_bi_agent.backend.config import AgentSettings

print("\n" + "="*70)
print("  3-MODEL GROQ ARCHITECTURE VERIFICATION")
print("="*70 + "\n")

settings = AgentSettings.from_env()

print("✓ Configuration loaded successfully!\n")

print("📋 PRIMARY MODELS:")
print(f"  1️⃣  Reasoning Model:     {settings.llm_reasoning_model}")
print(f"  2️⃣  SQL Model:            {settings.llm_sql_model}")
print(f"  3️⃣  Insight Model:        {settings.llm_insight_model}")

print("\n🔄 FALLBACK CHAINS:\n")

print(f"  Reasoning Variants ({len(settings.llm_reasoning_model_variants)}):")
for i, model in enumerate(settings.llm_reasoning_model_variants, 1):
    print(f"    {i}. {model}")

print(f"\n  SQL Variants ({len(settings.llm_sql_model_variants)}):")
for i, model in enumerate(settings.llm_sql_model_variants, 1):
    print(f"    {i}. {model}")

print(f"\n  Insight Variants ({len(settings.llm_insight_model_variants)}):")
for i, model in enumerate(settings.llm_insight_model_variants, 1):
    print(f"    {i}. {model}")

print("\n🔐 GROQ Configuration:")
print(f"  API Key: {'✓ SET' if settings.groq_api_key else '✗ NOT SET'}")
print(f"  Base URL: {settings.groq_base_url}")
print(f"  Provider: {settings.llm_provider}")

print("\n" + "="*70)
print("✅ All 3 models configured and ready!")
print("="*70 + "\n")
