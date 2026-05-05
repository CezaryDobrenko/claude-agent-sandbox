FROM python:3.13-slim-trixie

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/app/.venv \
    PATH="/app/.venv/bin:$PATH" \
    AGENT_WORKSPACE=/workspace \
    ANTHROPIC_MODEL=claude-sonnet-4-6 \
    MAX_AGENT_STEPS=20 \
    AGENT_MAX_TOKENS=500 \
    SHELL_TIMEOUT_SECONDS=60

RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    build-essential \
    ca-certificates \
    coreutils \
    curl \
    dnsutils \
    findutils \
    gcc \
    git \
    grep \
    iputils-ping \
    jq \
    sed \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

COPY pyproject.toml uv.lock README.md ./

RUN uv sync --frozen --no-dev

COPY . .

RUN useradd -m -u 10001 agent \
    && mkdir -p /workspace \
    && chown -R agent:agent /app /workspace

USER agent

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]