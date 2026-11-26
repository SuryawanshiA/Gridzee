"""Calls Claude and returns text or parsed JSON.

Providers (``AI_PROVIDER``):
    anthropic        Anthropic API, needs ANTHROPIC_API_KEY
    bedrock          Amazon Bedrock (bedrock-mantle), AWS credentials from the environment
    bedrock-runtime  Amazon Bedrock InvokeModel API, AWS credentials from the environment

The anthropic package is imported only here, so the test framework never needs it.
Responses are streamed, because generated code can be long.
"""

import json
import re
from typing import Any

from ai_engine import settings
from ai_engine.settings import PROMPTS


class AIError(RuntimeError):
    pass


def _client():
    try:
        import anthropic
    except ImportError as error:
        raise AIError("The 'anthropic' package is not installed. Run: pip install -r ai_engine/requirements.txt") from error

    if settings.AI_PROVIDER == "anthropic":
        return anthropic.Anthropic()
    if settings.AI_PROVIDER == "bedrock":
        return anthropic.AnthropicBedrockMantle()
    if settings.AI_PROVIDER == "bedrock-runtime":
        return anthropic.AnthropicBedrock()
    raise AIError(f"Unknown AI_PROVIDER '{settings.AI_PROVIDER}'. Use anthropic, bedrock or bedrock-runtime.")


def load_prompt(name: str, **values: str) -> str:
    """Read ``prompts/<name>.md`` and replace ``<<KEY>>`` placeholders."""
    text = (PROMPTS / f"{name}.md").read_text(encoding="utf-8")
    for key, value in values.items():
        text = text.replace(f"<<{key.upper()}>>", value)
    return text


def complete(system: str, user: str) -> str:
    if not settings.AI_MODEL:
        raise AIError("AI_MODEL is not set. Add it to .env (see .env.example).")
    client = _client()
    with client.messages.stream(
        model=settings.AI_MODEL,
        max_tokens=settings.AI_MAX_TOKENS,
        system=system,
        messages=[{"role": "user", "content": user}],
    ) as stream:
        message = stream.get_final_message()
    if message.stop_reason == "max_tokens":
        raise AIError("The response was cut off at AI_MAX_TOKENS. Raise AI_MAX_TOKENS or approve fewer scenarios at once.")
    return "".join(block.text for block in message.content if block.type == "text")


def complete_json(system: str, user: str) -> Any:
    return extract_json(complete(system, user))


def extract_json(text: str) -> Any:
    """Parse the first JSON object in the reply, with or without a ```json fence."""
    fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL)
    candidate = fenced.group(1) if fenced else text[text.find("{"): text.rfind("}") + 1]
    try:
        return json.loads(candidate)
    except json.JSONDecodeError as error:
        raise AIError(f"The AI reply was not valid JSON: {error}") from error
