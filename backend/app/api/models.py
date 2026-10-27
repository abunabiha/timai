from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user, require_role
from app.db.models import Model, Provider, User
from app.db.session import get_db
from app.gateway.gateway import model_gateway
from app.schemas.model import (
    ModelCreateRequest,
    ModelHealthCheckResponse,
    ModelResponse,
    ModelUpdateRequest,
)

router = APIRouter(prefix="/models", tags=["models"])


@router.get("", response_model=list[ModelResponse])
async def list_models(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    provider_id: Annotated[str | None, Query()] = None,
    tier: Annotated[str | None, Query()] = None,
    is_active: Annotated[bool | None, Query()] = None,
) -> list[ModelResponse]:
    """List models in the catalog, optionally filtered by provider, tier, or active status."""
    stmt = select(Model)
    if provider_id:
        stmt = stmt.where(Model.provider_id == provider_id)
    if tier:
        stmt = stmt.where(Model.tier == tier.lower())
    if is_active is not None:
        stmt = stmt.where(Model.is_active == is_active)

    stmt = stmt.order_by(Model.tier.desc(), Model.name.asc())
    result = await db.execute(stmt)
    models = result.scalars().all()
    return [ModelResponse.model_validate(m) for m in models]


@router.get("/{model_id}", response_model=ModelResponse)
async def get_model(
    model_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ModelResponse:
    """Get details of a specific model."""
    result = await db.execute(select(Model).where(Model.id == model_id))
    model = result.scalar_one_or_none()
    if model is None:
        raise HTTPException(status_code=404, detail="Model not found")
    return ModelResponse.model_validate(model)


@router.post("", response_model=ModelResponse, status_code=status.HTTP_201_CREATED)
async def create_model(
    payload: ModelCreateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role(["admin"]))],
) -> ModelResponse:
    """Add a new model to the catalog (Admin only)."""
    # Check if provider exists
    prov_res = await db.execute(select(Provider).where(Provider.id == payload.provider_id))
    if not prov_res.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Provider not found")

    model = Model(
        provider_id=payload.provider_id,
        name=payload.name,
        model_identifier=payload.model_identifier,
        context_window=payload.context_window,
        input_price=payload.input_price,
        output_price=payload.output_price,
        supports_tools=payload.supports_tools,
        supports_vision=payload.supports_vision,
        competency_score=payload.competency_score,
        tier=payload.tier.lower(),
        is_active=True,
    )
    db.add(model)
    await db.commit()
    await db.refresh(model)
    return ModelResponse.model_validate(model)


@router.put("/{model_id}", response_model=ModelResponse)
async def update_model(
    model_id: str,
    payload: ModelUpdateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role(["admin"]))],
) -> ModelResponse:
    """Update model configuration, tier, price, or competency score (Admin only)."""
    result = await db.execute(select(Model).where(Model.id == model_id))
    model = result.scalar_one_or_none()
    if model is None:
        raise HTTPException(status_code=404, detail="Model not found")

    update_data = payload.model_dump(exclude_unset=True)
    if "tier" in update_data and update_data["tier"] is not None:
        update_data["tier"] = update_data["tier"].lower()

    for field, value in update_data.items():
        setattr(model, field, value)

    await db.commit()
    await db.refresh(model)
    return ModelResponse.model_validate(model)


@router.delete("/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_model(
    model_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role(["admin"]))],
) -> None:
    """Delete a model from the catalog (Admin only)."""
    result = await db.execute(select(Model).where(Model.id == model_id))
    model = result.scalar_one_or_none()
    if model is None:
        raise HTTPException(status_code=404, detail="Model not found")

    await db.delete(model)
    await db.commit()


@router.post("/{model_id}/health-check", response_model=ModelHealthCheckResponse)
async def health_check_model(
    model_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role(["admin"]))],
) -> ModelHealthCheckResponse:
    """Perform a live health check on a model (Admin only)."""
    is_healthy, message = await model_gateway.health_check_model(db, model_id)
    result = await db.execute(select(Model).where(Model.id == model_id))
    model = result.scalar_one_or_none()
    model_name = model.name if model else "Unknown"

    return ModelHealthCheckResponse(
        model_id=model_id,
        model_name=model_name,
        is_healthy=is_healthy,
        message=message,
    )
