import asyncio
import shlex

from config import Config
from typing import Any, Literal
from helper import _ensure_workspace, _resolve_workspace_path, _truncate


def list_files(path: str = ".") -> str:
    target = _resolve_workspace_path(path)
    if not target.exists():
        return f"Path does not exist: {path}"
    if target.is_file():
        return str(target.relative_to(Config.WORKSPACE))

    lines: list[str] = []
    for item in sorted(target.rglob("*")):
        rel = item.relative_to(Config.WORKSPACE)
        if any(part in {".git", ".venv", "__pycache__", "node_modules"} for part in rel.parts):
            continue
        suffix = "/" if item.is_dir() else ""
        lines.append(f"{rel}{suffix}")
        if len(lines) >= 500:
            lines.append("[truncated to 500 entries]")
            break
    return "\n".join(lines) or "[empty]"


def read_file(path: str) -> str:
    target = _resolve_workspace_path(path)
    if not target.is_file():
        return f"Not a file: {path}"
    return _truncate(target.read_text(encoding="utf-8", errors="replace"))


def write_file(path: str, content: str, mode: Literal["overwrite", "append"] = "overwrite") -> str:
    target = _resolve_workspace_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    if mode == "append":
        with target.open("a", encoding="utf-8") as handle:
            handle.write(content)
    else:
        target.write_text(content, encoding="utf-8")
    return f"Wrote {len(content)} bytes to {target.relative_to(Config.WORKSPACE)} using mode={mode}."


async def run_shell(command: str) -> str:
    _ensure_workspace()
    process = await asyncio.create_subprocess_exec(
        "/bin/bash",
        "-lc",
        command,
        cwd=str(Config.WORKSPACE),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=Config.SHELL_TIMEOUT_SECONDS)
    except TimeoutError:
        process.kill()
        await process.communicate()
        return f"Command timed out after {Config.SHELL_TIMEOUT_SECONDS}s: {shlex.quote(command)}"

    out = stdout.decode(errors="replace")
    err = stderr.decode(errors="replace")
    combined = f"exit_code={process.returncode}\n\nSTDOUT:\n{out}\nSTDERR:\n{err}".strip()
    return _truncate(combined)


TOOLS: list[dict[str, Any]] = [
    {
        "name": "list_files",
        "description": "List files and directories under the container workspace.",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "Workspace-relative path."}},
            "required": [],
        },
    },
    {
        "name": "read_file",
        "description": "Read a UTF-8 text file from the container workspace.",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "Workspace-relative file path."}},
            "required": ["path"],
        },
    },
    {
        "name": "write_file",
        "description": "Create or edit a UTF-8 text file in the container workspace.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Workspace-relative file path."},
                "content": {"type": "string", "description": "Full content to write or append."},
                "mode": {"type": "string", "enum": ["overwrite", "append"], "default": "overwrite"},
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "run_shell",
        "description": "Run a shell command inside the container workspace. Internet access is available if Docker networking and DNS allow it. Use for git, python, curl, tests, package inspection, etc.",
        "input_schema": {
            "type": "object",
            "properties": {"command": {"type": "string", "description": "Shell command to run."}},
            "required": ["command"],
        },
    },
]


async def _execute_tool(name: str, tool_input: dict[str, Any]) -> str:
    if name == "list_files":
        return list_files(tool_input.get("path", "."))

    if name == "read_file":
        path = tool_input.get("path")
        if not isinstance(path, str) or not path.strip():
            raise ValueError("read_file requires a non-empty string field: path")
        return read_file(path)

    if name == "write_file":
        path = tool_input.get("path")
        content = tool_input.get("content")
        mode = tool_input.get("mode", "overwrite")

        if not isinstance(path, str) or not path.strip():
            raise ValueError("write_file requires a non-empty string field: path")
        if not isinstance(content, str):
            raise ValueError(
                "write_file requires field: content. "
                "Call write_file with both path and content, for example: "
                '{"path":"file.py","content":"print(123)\\n"}'
            )
        if mode not in {"overwrite", "append"}:
            raise ValueError("write_file mode must be either 'overwrite' or 'append'")

        return write_file(path=path, content=content, mode=mode)

    if name == "run_shell":
        command = tool_input.get("command")
        if not isinstance(command, str) or not command.strip():
            raise ValueError(
                "run_shell requires field: command. "
                'Example: {"command":"python file.py"}'
            )
        return await run_shell(command)

    raise ValueError(f"Unknown tool: {name}")