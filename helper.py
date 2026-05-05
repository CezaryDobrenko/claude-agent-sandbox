from pathlib import Path

from config import Config


def _ensure_workspace() -> None:
    Config.WORKSPACE.mkdir(parents=True, exist_ok=True)


def _resolve_workspace_path(path: str) -> Path:
    _ensure_workspace()

    raw = Path(path)

    if raw.is_absolute():
        candidate = raw.resolve()
    else:
        candidate = (Config.WORKSPACE / raw).resolve()

    if candidate != Config.WORKSPACE and Config.WORKSPACE not in candidate.parents:
        raise ValueError(f"Path escapes workspace: {path}")

    return candidate


def _truncate(text: str, limit: int = Config.MAX_SHELL_OUTPUT_CHARS) -> str:
    if len(text) <= limit:
        return text

    head = limit // 3
    tail = limit - head
    return (
        text[:head]
        + f"\n\n[... truncated {len(text) - limit} chars ...]\n\n"
        + text[-tail:]
    )

