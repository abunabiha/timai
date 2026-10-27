import time
from typing import Any

from app.gateway.base import BaseAdapter, ModelGatewayRequest, ModelGatewayResponse


class FakeProviderAdapter(BaseAdapter):
    """
    Fake Provider Adapter for automated testing.
    Provides deterministic responses without consuming real LLM API tokens.
    """

    def __init__(
        self,
        default_reply: str = "This is a deterministic response from FakeProvider.",
        should_fail: bool = False,
        mismatch_actual_model: str | None = None,
    ) -> None:
        self.default_reply = default_reply
        self.should_fail = should_fail
        self.failure_message = "Simulated failure in FakeProvider"
        self.mismatch_actual_model = mismatch_actual_model
        self.custom_responses: dict[str, dict[str, Any]] = {}
        self.call_history: list[dict[str, Any]] = []

    def register_response(
        self,
        pattern: str,
        reply: str,
        prompt_tokens: int | None = None,
        completion_tokens: int | None = None,
    ) -> None:
        """Register a deterministic reply when pattern is contained in messages."""
        self.custom_responses[pattern] = {
            "reply": reply,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
        }

    def set_should_fail(self, should_fail: bool = True, error_msg: str = "Simulated failure") -> None:
        """Configure simulated failure."""
        self.should_fail = should_fail
        self.failure_message = error_msg

    def set_actual_model_override(self, actual_model: str | None) -> None:
        """Override actual model returned to test model mismatch."""
        self.mismatch_actual_model = actual_model

    async def complete(
        self,
        model_name: str,
        request: ModelGatewayRequest,
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> ModelGatewayResponse:
        start_time = time.perf_counter()

        self.call_history.append({
            "model_name": model_name,
            "messages": request.messages,
            "tools": request.tools,
            "limits": request.limits,
            "timestamp": time.time(),
        })

        if self.should_fail:
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            return ModelGatewayResponse(
                content="",
                requested_model=model_name,
                actual_model=model_name,
                input_tokens=0,
                output_tokens=0,
                cost=0.0,
                latency_ms=latency_ms,
                error=f"{self.failure_message} for model {model_name}",
            )

        # Match custom responses
        matched_reply = self.default_reply
        custom_input_tokens = None
        custom_output_tokens = None

        full_content = " ".join(m.get("content", "") for m in request.messages)
        for pattern, res in self.custom_responses.items():
            if pattern in full_content:
                matched_reply = res["reply"]
                custom_input_tokens = res["prompt_tokens"]
                custom_output_tokens = res["completion_tokens"]
                break

        # Calculate simulated token counts based on length or custom
        input_text = request.agent_context + " " + full_content
        input_tokens = custom_input_tokens if custom_input_tokens is not None else max(1, len(input_text.split()))
        output_tokens = custom_output_tokens if custom_output_tokens is not None else max(1, len(matched_reply.split()))

        # Simulated pricing: $1 / 1M input, $3 / 1M output
        cost = (input_tokens * 1.0 + output_tokens * 3.0) / 1_000_000.0
        latency_ms = max(5, int((time.perf_counter() - start_time) * 1000))

        actual_model = self.mismatch_actual_model if self.mismatch_actual_model else model_name
        warning = None
        if actual_model != model_name:
            warning = f"Model mismatch: requested '{model_name}' but provider returned '{actual_model}'"

        return ModelGatewayResponse(
            content=matched_reply,
            requested_model=model_name,
            actual_model=actual_model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=round(cost, 6),
            latency_ms=latency_ms,
            warning=warning,
            error=None,
        )

    async def health_check(
        self,
        model_name: str,
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> bool:
        return not self.should_fail
