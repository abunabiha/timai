from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ModelGatewayRequest:
    agent_context: str
    messages: list[dict[str, str]]
    tools: list[dict[str, Any]] | None = None
    limits: dict[str, Any] | None = None
    max_tokens: int = 2000
    temperature: float = 0.7


@dataclass
class ModelGatewayResponse:
    content: str
    requested_model: str
    actual_model: str
    input_tokens: int
    output_tokens: int
    cost: float
    latency_ms: int
    is_fallback: bool = False
    warning: str | None = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseAdapter(ABC):
    """Abstract interface for all model provider adapters."""

    @abstractmethod
    async def complete(
        self,
        model_name: str,
        request: ModelGatewayRequest,
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> ModelGatewayResponse:
        """Execute a completion request."""
        pass

    @abstractmethod
    async def health_check(
        self,
        model_name: str,
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> bool:
        """Check availability of the model."""
        pass
