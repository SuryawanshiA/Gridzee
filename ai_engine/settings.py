"""Paths and AI settings for the AI engine.

AI settings come from environment variables (``.env`` locally):
    AI_PROVIDER     anthropic (default) | bedrock | bedrock-runtime
    AI_MODEL        model name, required (no default, so an outdated name is never used silently)
    AI_MAX_TOKENS   max output tokens per request (default 32000)
    ANTHROPIC_API_KEY   for AI_PROVIDER=anthropic
    AWS credentials / AWS_REGION   for the Bedrock providers
"""

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env", override=False)

SRC = ROOT / "src" / "gridzee_qa"
TESTS = ROOT / "tests"
PROMPTS = Path(__file__).resolve().parent / "prompts"

WORKSPACE = ROOT / "ai_workspace"
EXPLORATION_DIR = WORKSPACE / "exploration"
PLANS_DIR = WORKSPACE / "plans"
GENERATED_DIR = WORKSPACE / "generated"
HEAL_DIR = WORKSPACE / "heal"
RUNS_DIR = WORKSPACE / "runs"

AI_PROVIDER = os.getenv("AI_PROVIDER", "anthropic").lower()
AI_MODEL = os.getenv("AI_MODEL", "")
AI_MAX_TOKENS = int(os.getenv("AI_MAX_TOKENS", "32000"))

MAX_RETRIES = 3
MAX_CONTEXT_CHARS = int(os.getenv("AI_MAX_CONTEXT_CHARS", "250000"))

# Where each stage may write. Paths are relative to ROOT.
GENERATOR_ALLOWED = (
    "src/gridzee_qa/pages/",
    "src/gridzee_qa/flows/",
    "src/gridzee_qa/components/",
    "src/gridzee_qa/factories/",
    "tests/ui/",
    "data/",
    "docs/test-cases/",
)
HEALER_ALLOWED = (
    "src/gridzee_qa/pages/",
    "src/gridzee_qa/components/",
)
# Never written by any stage, even inside an allowed folder.
ALWAYS_BLOCKED = ("tests/conftest.py", ".env", ".auth/")
