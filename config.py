import os
from pathlib import Path


class Config:
    WORKSPACE = Path(os.getenv("AGENT_WORKSPACE", "/workspace")).resolve()
    DEFAULT_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5")
    AGENT_MAX_TOKENS = int(os.getenv("AGENT_MAX_TOKENS", "1000"))
    MAX_AGENT_STEPS = int(os.getenv("MAX_AGENT_STEPS", "20"))
    MAX_SHELL_OUTPUT_CHARS = int(os.getenv("MAX_SHELL_OUTPUT_CHARS", "4000"))
    SHELL_TIMEOUT_SECONDS = int(os.getenv("SHELL_TIMEOUT_SECONDS", "60"))