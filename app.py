import os
from datetime import datetime, timezone

from anthropic import Anthropic
from fastapi import FastAPI, HTTPException
from config import Config
from dto import AgentRunRequest, AgentRunResponse, HealthResponse, ToolCall
from typing import Any
from helper import _ensure_workspace
from tool import TOOLS, _execute_tool


app = FastAPI(
    title="AI Agent Sandbox",
    version="1.0.0",
    description="FastAPI service exposing a Claude Sonnet agent that can work inside a container workspace.",
)


@app.get("/", tags=["root"])
def read_root() -> dict[str, Any]:
    return {
        "message": "AI agent sandbox is alive",
        "docs": "/docs",
        "workspace": str(Config.WORKSPACE),
        "model": Config.DEFAULT_MODEL,
    }


@app.get("/health", response_model=HealthResponse, tags=["health"])
def health_check() -> HealthResponse:
    return HealthResponse(status="ok", timestamp=datetime.now(timezone.utc).isoformat())


@app.post("/agent/run", response_model=AgentRunResponse, tags=["agent"])
async def run_agent(request: AgentRunRequest) -> AgentRunResponse:
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise HTTPException(status_code=500, detail="Missing ANTHROPIC_API_KEY environment variable.")

    _ensure_workspace()
    client = Anthropic()
    model = request.model or Config.DEFAULT_MODEL
    max_tokens = request.max_tokens or Config.AGENT_MAX_TOKENS
    messages: list[dict[str, Any]] = [{"role": "user", "content": request.prompt}]
    tool_log: list[ToolCall] = []
    final_answer = ""
    
    workspace_path = Config.WORKSPACE
    project_path = workspace_path / "project"
    system_prompt = f"""
You are an autonomous coding agent running inside a Docker container.

Your writable workspace is {workspace_path}. Keep all file operations inside this workspace.

The user's project files are mounted at {project_path}.
This directory maps to the user's local folder.
Treat {project_path} as the project root for all user-provided code.

Important:
- When the user asks about "the project", "the codebase", "my app", "the uploaded files", or similar, inspect {project_path} first.
- Be careful and prefer minimal, targeted edits.
- Do not delete, overwrite, or restructure large parts of the project unless the user explicitly asks.

File tool path rules:
- Use workspace-relative paths with file tools.
- For project files, use paths like "project/README.md", "project/src/main.py", or "project/package.json".
- Do not use absolute paths like "{project_path}/README.md" with file tools.
- Never write outside {workspace_path}.

Shell command rules:
- Run project commands from the project root using: cd "{project_path}" && <command>
- Prefer targeted commands over broad destructive commands.
- Before destructive operations, prefer making the smallest safe change.
- Do not run commands that delete the whole project unless the user explicitly asks.

Tool usage rules:
- When using tools, always provide all required input fields.
- write_file requires both "path" and "content".
- run_shell requires "command".
- If a tool call fails because of missing fields, retry once with the complete input.
- Do not repeat the same failed tool call multiple times.

Be concise:
- Before tool calls, write at most one short sentence.
- After tool calls, do not restate tool output.
- Final answer: max 8 bullets unless the user asks for more.
- Prefer small diffs over full file rewrites.
- Read only files that are relevant to the task.

You may use shell commands, create files, edit files, run tests, inspect the project, and use internet access through commands such as curl or git when available.

At the end, summarize what you changed and mention any commands or tests you ran.
""".strip()

    for _ in range(request.max_steps):
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=messages,
            tools=TOOLS,
        )
        assistant_content = [block.model_dump() for block in response.content]
        messages.append({"role": "assistant", "content": assistant_content})

        tool_results: list[dict[str, Any]] = []
        text_parts: list[str] = []
        for block in response.content:
            if block.type == "text":
                text_parts.append(block.text)
                continue
            if block.type != "tool_use":
                continue

            is_error = False
            try:
                result = await _execute_tool(block.name, dict(block.input))
            except Exception as exc:  # noqa: BLE001 - return tool errors to Claude
                is_error = True
                result = f"ERROR: {type(exc).__name__}: {exc}"

            tool_log.append(ToolCall(name=block.name, input=dict(block.input), result=result, is_error=is_error))
            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                    "is_error": is_error,
                }
            )

        if text_parts:
            final_answer = "\n".join(text_parts)

        if not tool_results:
            return AgentRunResponse(model=model, answer=final_answer.strip(), tool_calls=tool_log)

        messages.append({"role": "user", "content": tool_results})

    return AgentRunResponse(
        model=model,
        answer=(final_answer.strip() or "Agent stopped after reaching max_steps."),
        tool_calls=tool_log,
    )