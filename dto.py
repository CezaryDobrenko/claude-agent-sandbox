from typing import Any
from pydantic import BaseModel, Field
from config import Config


class HealthResponse(BaseModel):
    status: str
    timestamp: str


class AgentRunRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="Task for the agent to perform inside the container.")
    model: str | None = Field(default=None, description="Optional Claude model override.")
    max_steps: int = Field(default=Config.MAX_AGENT_STEPS, ge=1, le=50)
    max_tokens: int = Field(default=Config.AGENT_MAX_TOKENS, ge=100, le=4000)


class ToolCall(BaseModel):
    name: str
    input: dict[str, Any]
    result: str
    is_error: bool = False


class AgentRunResponse(BaseModel):
    model: str
    answer: str
    tool_calls: list[ToolCall]