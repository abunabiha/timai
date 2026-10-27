import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.crypto import decrypt_secret
from app.db.models import Model, UsageRecord
from app.gateway.adapters import AnthropicAdapter, GoogleAdapter, OpenAIAdapter, OpenRouterAdapter
from app.gateway.base import BaseAdapter, ModelGatewayRequest, ModelGatewayResponse
from app.gateway.fake import FakeProviderAdapter

logger = logging.getLogger("timai.gateway")

TIER_ORDER = {
    "low": 1,
    "medium": 2,
    "high": 3,
    "xhigh": 4,
}


class ModelGateway:
    """
    Central gateway for all model interactions.
    Handles routing, adapters, fallback logic, actual model verification, and usage recording.
    """

    def __init__(self) -> None:
        self.adapters: dict[str, BaseAdapter] = {
            "fake": FakeProviderAdapter(),
            "openai": OpenAIAdapter(),
            "anthropic": AnthropicAdapter(),
            "google": GoogleAdapter(),
            "openrouter": OpenRouterAdapter(),
        }
        self.fake_adapter = self.adapters["fake"]

    def register_adapter(self, provider_type: str, adapter: BaseAdapter) -> None:
        """Register or override an adapter for a given provider type."""
        self.adapters[provider_type.lower()] = adapter
        if provider_type.lower() == "fake" and isinstance(adapter, FakeProviderAdapter):
            self.fake_adapter = adapter

    def set_fake_adapter(self, adapter: FakeProviderAdapter) -> None:
        """Allow injecting a customized FakeProvider for tests."""
        self.fake_adapter = adapter
        self.adapters["fake"] = adapter

    def get_adapter(self, provider_type: str) -> BaseAdapter:
        return self.adapters.get(provider_type.lower(), self.fake_adapter)

    def is_tier_eligible_for_fallback(self, original_tier: str, fallback_tier: str) -> bool:
        """Verify fallback tier is equal to or higher than original tier."""
        orig = TIER_ORDER.get(original_tier.lower(), 1)
        fall = TIER_ORDER.get(fallback_tier.lower(), 1)
        return fall >= orig

    async def complete(
        self,
        agent_context: str,
        messages: list[dict[str, str]],
        tools: list[dict[str, Any]] | None = None,
        limits: dict[str, Any] | None = None,
        model: Model | str | None = None,
        fallback_model: Model | str | None = None,
        db: AsyncSession | None = None,
        project_id: str | None = None,
        agent_id: str | None = None,
    ) -> ModelGatewayResponse:
        """Execute completion through model gateway with fallback and usage logging."""
        request = ModelGatewayRequest(
            agent_context=agent_context,
            messages=messages,
            tools=tools,
            limits=limits,
        )

        # Resolve primary Model entity if string ID is passed
        primary_model: Model | None = None
        if isinstance(model, Model):
            primary_model = model
        elif isinstance(model, str) and db is not None:
            res = await db.execute(
                select(Model).options(selectinload(Model.provider)).where(Model.id == model)
            )
            primary_model = res.scalar_one_or_none()

        # Resolve fallback Model entity if string ID is passed
        resolved_fallback: Model | None = None
        if isinstance(fallback_model, Model):
            resolved_fallback = fallback_model
        elif isinstance(fallback_model, str) and db is not None:
            res = await db.execute(
                select(Model).options(selectinload(Model.provider)).where(Model.id == fallback_model)
            )
            resolved_fallback = res.scalar_one_or_none()

        # If no fallback explicitly provided, discover active candidate with tier >= primary
        if resolved_fallback is None and primary_model is not None and db is not None:
            orig_tier_val = TIER_ORDER.get(primary_model.tier.lower(), 1)
            cand_res = await db.execute(
                select(Model)
                .options(selectinload(Model.provider))
                .where(Model.is_active.is_(True), Model.id != primary_model.id)
            )
            candidates = cand_res.scalars().all()
            for cand in candidates:
                cand_tier_val = TIER_ORDER.get(cand.tier.lower(), 1)
                if cand_tier_val >= orig_tier_val:
                    resolved_fallback = cand
                    break

        model_name = primary_model.model_identifier if primary_model else "fake-model"
        provider_type = primary_model.provider.provider_type if (primary_model and primary_model.provider) else "fake"
        api_key = decrypt_secret(primary_model.provider.api_key_encrypted) if (primary_model and primary_model.provider and primary_model.provider.api_key_encrypted) else None
        base_url = primary_model.provider.base_url if (primary_model and primary_model.provider and primary_model.provider.base_url) else None

        adapter = self.get_adapter(provider_type)

        # 1. Attempt call with primary model
        response = await adapter.complete(
            model_name=model_name,
            request=request,
            api_key=api_key,
            base_url=base_url,
        )

        # 2. Check for fallback if error occurred
        if response.error and resolved_fallback is not None:
            orig_tier = primary_model.tier if primary_model else "medium"
            fall_tier = resolved_fallback.tier
            if self.is_tier_eligible_for_fallback(orig_tier, fall_tier):
                logger.warning(
                    "Primary model %s failed: %s. Initiating fallback to %s (tier: %s >= %s)",
                    model_name,
                    response.error,
                    resolved_fallback.model_identifier,
                    fall_tier,
                    orig_tier,
                )

                fall_provider_type = resolved_fallback.provider.provider_type if resolved_fallback.provider else "fake"
                fall_api_key = decrypt_secret(resolved_fallback.provider.api_key_encrypted) if (resolved_fallback.provider and resolved_fallback.provider.api_key_encrypted) else None
                fall_base_url = resolved_fallback.provider.base_url if resolved_fallback.provider else None
                fall_adapter = self.get_adapter(fall_provider_type)

                fallback_response = await fall_adapter.complete(
                    model_name=resolved_fallback.model_identifier,
                    request=request,
                    api_key=fall_api_key,
                    base_url=fall_base_url,
                )
                fallback_response.is_fallback = True
                fallback_response.requested_model = model_name
                fallback_response.warning = f"Fallback triggered from {model_name} to {resolved_fallback.model_identifier}"
                response = fallback_response
            else:
                logger.error(
                    "Fallback model %s has tier %s, lower than required %s. Fallback rejected.",
                    resolved_fallback.model_identifier,
                    fall_tier,
                    orig_tier,
                )

        # 3. Mismatch warning between requested and actual model
        if response.actual_model != response.requested_model and not response.is_fallback:
            warning_msg = f"Model mismatch: requested model '{response.requested_model}' but actual model is '{response.actual_model}'"
            response.warning = warning_msg
            logger.warning(warning_msg)

        # 4. Record UsageRecord in Database
        if db is not None:
            usage = UsageRecord(
                project_id=project_id,
                agent_id=agent_id,
                requested_model=response.requested_model,
                actual_model=response.actual_model,
                input_tokens=response.input_tokens,
                output_tokens=response.output_tokens,
                cost=response.cost,
                latency_ms=response.latency_ms,
                error_message=response.error,
            )
            db.add(usage)
            await db.commit()

        return response

    async def health_check_model(
        self,
        db: AsyncSession,
        model_id: str,
    ) -> tuple[bool, str]:
        """Run health check against a registered model by id."""
        res = await db.execute(
            select(Model).options(selectinload(Model.provider)).where(Model.id == model_id)
        )
        model = res.scalar_one_or_none()
        if not model:
            return False, "Model not found in database"

        provider_type = model.provider.provider_type if model.provider else "fake"
        api_key = decrypt_secret(model.provider.api_key_encrypted) if (model.provider and model.provider.api_key_encrypted) else None
        base_url = model.provider.base_url if model.provider else None
        adapter = self.get_adapter(provider_type)

        try:
            is_healthy = await adapter.health_check(model.model_identifier, api_key=api_key, base_url=base_url)
            if is_healthy:
                return True, f"Model {model.name} is healthy and responsive"
            return False, f"Model {model.name} reported unhealthy status"
        except Exception as exc:
            return False, f"Health check failed: {exc}"


model_gateway = ModelGateway()
