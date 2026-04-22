from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class LlmConfig:
    provider: str
    model: str
    api_key_env: str
    timeout_s: float
    max_retries: int


def load_llm_config() -> LlmConfig | None:
    """
    Phase 2:
    - LLM_PROVIDER: "groq" (default)
    - GROQ_MODEL: e.g. "llama-3.1-8b-instant" (default)
    - GROQ_API_KEY: required for provider=groq
    - GROQ_TIMEOUT_S: request timeout seconds (default 60)
    - GROQ_MAX_RETRIES: SDK-level retries (default 3)
    """
    provider = os.getenv("LLM_PROVIDER", "groq").strip().casefold()
    if provider == "groq":
        api_key_env = "GROQ_API_KEY"
        api_key = os.getenv(api_key_env)
        if not api_key:
            return None
        model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant").strip()
        timeout_s = float(os.getenv("GROQ_TIMEOUT_S", "60"))
        max_retries = int(os.getenv("GROQ_MAX_RETRIES", "3"))
        return LlmConfig(
            provider=provider,
            model=model,
            api_key_env=api_key_env,
            timeout_s=timeout_s,
            max_retries=max_retries,
        )
    return None


def chat_json(*, system: str, user: str, config: LlmConfig) -> tuple[str, dict]:
    if config.provider != "groq":
        raise ValueError(f"Unsupported provider: {config.provider}")

    from groq import Groq

    client = Groq(
        api_key=os.environ[config.api_key_env],
        timeout=config.timeout_s,
        max_retries=config.max_retries,
    )
    resp = client.chat.completions.create(
        model=config.model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.3,
        response_format={"type": "json_object"},
    )
    
    content = resp.choices[0].message.content or ""
    usage = {
        "prompt_tokens": resp.usage.prompt_tokens if resp.usage else 0,
        "completion_tokens": resp.usage.completion_tokens if resp.usage else 0,
    }
    
    return content, usage
