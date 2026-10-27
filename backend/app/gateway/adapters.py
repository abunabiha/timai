import logging
import time
from typing import Any
from app.gateway.base import BaseAdapter, ModelGatewayRequest, ModelGatewayResponse

logger = logging.getLogger(__name__)


class LiteLLMAdapter(BaseAdapter):
    """
    Adapter leveraging LiteLLM underneath for unified provider communications
    (OpenAI-compatible, Anthropic, Google Vertex/AI Studio, OpenRouter).
    """

    def __init__(self, provider_prefix: str = "") -> None:
        self.provider_prefix = provider_prefix

    def _format_model(self, model_name: str) -> str:
        if self.provider_prefix and not model_name.startswith(self.provider_prefix):
            return f"{self.provider_prefix}/{model_name}"
        return model_name

    async def complete(
        self,
        model_name: str,
        request: ModelGatewayRequest,
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> ModelGatewayResponse:
        start_time = time.perf_counter()
        formatted_model = self._format_model(model_name)

        messages: list[dict[str, Any]] = []
        if request.agent_context:
            messages.append({"role": "system", "content": request.agent_context})
        messages.extend(request.messages)

        try:
            import litellm

            litellm_kwargs: dict[str, Any] = {
                "model": formatted_model,
                "messages": messages,
                "temperature": request.temperature,
                "max_tokens": request.max_tokens,
            }
            if api_key:
                litellm_kwargs["api_key"] = api_key
            if base_url:
                litellm_kwargs["api_base"] = base_url
            if request.tools:
                litellm_kwargs["tools"] = request.tools

            response = await litellm.acompletion(**litellm_kwargs)
            latency_ms = int((time.perf_counter() - start_time) * 1000)

            content = response.choices[0].message.content or ""
            actual_model = getattr(response, "model", model_name)
            usage = getattr(response, "usage", None)

            input_tokens = getattr(usage, "prompt_tokens", 0) if usage else 0
            output_tokens = getattr(usage, "completion_tokens", 0) if usage else 0

            # Calculate cost via litellm if available
            try:
                cost = litellm.completion_cost(completion_response=response)
            except Exception:
                cost = 0.0

            warning = None
            if actual_model and actual_model != model_name and not actual_model.endswith(model_name):
                warning = f"Model mismatch: requested '{model_name}', got '{actual_model}'"

            return ModelGatewayResponse(
                content=content,
                requested_model=model_name,
                actual_model=actual_model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost=cost,
                latency_ms=latency_ms,
                warning=warning,
                error=None,
            )

        except Exception as exc:
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            logger.error("LiteLLM completion error for model %s: %s", model_name, exc)
            return ModelGatewayResponse(
                content="",
                requested_model=model_name,
                actual_model=model_name,
                input_tokens=0,
                output_tokens=0,
                cost=0.0,
                latency_ms=latency_ms,
                error=str(exc),
            )

    async def health_check(
        self,
        model_name: str,
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> bool:
        dummy_request = ModelGatewayRequest(
            agent_context="ping",
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=5,
        )
        res = await self.complete(model_name, dummy_request, api_key=api_key, base_url=base_url)
        return res.error is None


class OpenAIAdapter(LiteLLMAdapter):
    def __init__(self) -> None:
        super().__init__(provider_prefix="openai")


class AnthropicAdapter(LiteLLMAdapter):
    def __init__(self) -> None:
        super().__init__(provider_prefix="anthropic")


class GoogleAdapter(LiteLLMAdapter):
    def __init__(self) -> None:
        super().__init__(provider_prefix="gemini")


class OpenRouterAdapter(LiteLLMAdapter):
    def __init__(self) -> None:
        super().__init__(provider_prefix="openrouter")
