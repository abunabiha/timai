import time
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import require_role
from app.core.crypto import decrypt_secret, encrypt_secret, mask_secret
from app.db.models import Provider, User
from app.db.session import get_db
from app.gateway.base import ModelGatewayRequest
from app.gateway.gateway import model_gateway
from app.schemas.provider import (
    ProviderCreateRequest,
    ProviderResponse,
    ProviderTestResponse,
)

router = APIRouter(prefix="/providers", tags=["providers"])


@router.get("", response_model=list[ProviderResponse])
async def list_providers(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role(["admin"]))],
) -> list[ProviderResponse]:
    """List all registered LLM providers (Admin only). API keys are masked and never exposed."""
    result = await db.execute(select(Provider).order_by(Provider.created_at.desc()))
    providers = result.scalars().all()

    response: list[ProviderResponse] = []
    for p in providers:
        has_key = bool(p.api_key_encrypted)
        decrypted = decrypt_secret(p.api_key_encrypted) if has_key else ""
        response.append(
            ProviderResponse(
                id=p.id,
                name=p.name,
                provider_type=p.provider_type,
                base_url=p.base_url,
                is_active=p.is_active,
                has_api_key=has_key,
                api_key_masked=mask_secret(decrypted) if has_key else "none",
                created_at=p.created_at,
            )
        )
    return response


@router.post("", response_model=ProviderResponse, status_code=status.HTTP_201_CREATED)
async def create_provider(
    payload: ProviderCreateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role(["admin"]))],
) -> ProviderResponse:
    """Create a new model provider. Stores API key encrypted with AES-256-GCM."""
    encrypted_key = encrypt_secret(payload.api_key) if payload.api_key else ""

    provider = Provider(
        name=payload.name,
        provider_type=payload.provider_type.lower(),
        base_url=payload.base_url,
        api_key_encrypted=encrypted_key,
        is_active=True,
    )
    db.add(provider)
    await db.commit()
    await db.refresh(provider)

    return ProviderResponse(
        id=provider.id,
        name=provider.name,
        provider_type=provider.provider_type,
        base_url=provider.base_url,
        is_active=provider.is_active,
        has_api_key=bool(payload.api_key),
        api_key_masked=mask_secret(payload.api_key) if payload.api_key else "none",
        created_at=provider.created_at,
    )


@router.post("/{provider_id}/test", response_model=ProviderTestResponse)
async def test_provider_connection(
    provider_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role(["admin"]))],
) -> ProviderTestResponse:
    """Test connection to a provider using its registered adapter."""
    result = await db.execute(select(Provider).where(Provider.id == provider_id))
    provider = result.scalar_one_or_none()
    if provider is None:
        raise HTTPException(status_code=404, detail="Provider not found")

    adapter = model_gateway.get_adapter(provider.provider_type)
    api_key = decrypt_secret(provider.api_key_encrypted) if provider.api_key_encrypted else None

    start = time.perf_counter()
    req = ModelGatewayRequest(
        agent_context="Connection test",
        messages=[{"role": "user", "content": "ping"}],
        max_tokens=10,
    )
    test_model = "test-model" if provider.provider_type == "fake" else "gpt-3.5-turbo"
    res = await adapter.complete(test_model, req, api_key=api_key, base_url=provider.base_url)
    latency_ms = int((time.perf_counter() - start) * 1000)

    if res.error:
        return ProviderTestResponse(
            provider_id=provider.id,
            success=False,
            message=f"Connection test failed: {res.error}",
            latency_ms=latency_ms,
        )

    return ProviderTestResponse(
        provider_id=provider.id,
        success=True,
        message=f"Connection successful! Response: '{res.content[:50]}...'",
        latency_ms=latency_ms,
    )


@router.delete("/{provider_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_provider(
    provider_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role(["admin"]))],
) -> None:
    """Delete a provider and associated models."""
    result = await db.execute(select(Provider).where(Provider.id == provider_id))
    provider = result.scalar_one_or_none()
    if provider is None:
        raise HTTPException(status_code=404, detail="Provider not found")

    await db.delete(provider)
    await db.commit()
