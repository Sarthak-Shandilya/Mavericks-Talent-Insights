"""System administrator API routes."""
from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from apis.deps import require_roles
from configs.constants import RoleName
from models.user import User
from schemas.admin import (
    AdminUserPatch,
    AdminUserRead,
    AuditLogRead,
    ClassificationOverrideCreate,
    ClassificationOverrideRead,
    RecomputeResponse,
    ScoringConfigCreate,
    ScoringConfigRead,
    TopperRuleCreate,
    TopperRuleRead,
    TopperRuleUpdate,
    UploadMonitorItem,
    UploadRowErrorRead,
)
from services import admin_service, audit_service
from utils.database import get_db

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/scoring-configs", response_model=list[ScoringConfigRead])
def get_scoring_configs(
    db: Annotated[Session, Depends(get_db)],
    _admin: Annotated[User, Depends(require_roles(RoleName.SYSTEM_ADMIN))],
) -> list[ScoringConfigRead]:
    return admin_service.list_scoring_configs(db)


@router.post("/scoring-configs", response_model=ScoringConfigRead, status_code=status.HTTP_201_CREATED)
def post_scoring_config(
    body: ScoringConfigCreate,
    db: Annotated[Session, Depends(get_db)],
    admin: Annotated[User, Depends(require_roles(RoleName.SYSTEM_ADMIN))],
) -> ScoringConfigRead:
    return admin_service.create_scoring_config(
        db,
        weights=body.weights,
        high_threshold=body.high_threshold,
        average_threshold=body.average_threshold,
        actor=admin,
    )


@router.put("/scoring-configs/{config_id}/activate", response_model=ScoringConfigRead)
def activate_scoring_config(
    config_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    admin: Annotated[User, Depends(require_roles(RoleName.SYSTEM_ADMIN))],
) -> ScoringConfigRead:
    return admin_service.activate_scoring_config(db, config_id, admin)


@router.get("/topper-rules", response_model=list[TopperRuleRead])
def get_topper_rules(
    db: Annotated[Session, Depends(get_db)],
    _admin: Annotated[User, Depends(require_roles(RoleName.SYSTEM_ADMIN))],
) -> list[TopperRuleRead]:
    return admin_service.list_topper_rules(db)


@router.post("/topper-rules", response_model=TopperRuleRead, status_code=status.HTTP_201_CREATED)
def post_topper_rule(
    body: TopperRuleCreate,
    db: Annotated[Session, Depends(get_db)],
    admin: Annotated[User, Depends(require_roles(RoleName.SYSTEM_ADMIN))],
) -> TopperRuleRead:
    return admin_service.create_topper_rule(db, body.model_dump(), admin)


@router.put("/topper-rules/{rule_id}", response_model=TopperRuleRead)
def put_topper_rule(
    rule_id: uuid.UUID,
    body: TopperRuleUpdate,
    db: Annotated[Session, Depends(get_db)],
    admin: Annotated[User, Depends(require_roles(RoleName.SYSTEM_ADMIN))],
) -> TopperRuleRead:
    return admin_service.update_topper_rule(db, rule_id, body.model_dump(exclude_unset=True), admin)


@router.delete("/topper-rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_topper_rule(
    rule_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    admin: Annotated[User, Depends(require_roles(RoleName.SYSTEM_ADMIN))],
) -> None:
    admin_service.delete_topper_rule(db, rule_id, admin)


@router.post("/recompute", response_model=RecomputeResponse)
def post_recompute(
    db: Annotated[Session, Depends(get_db)],
    admin: Annotated[User, Depends(require_roles(RoleName.SYSTEM_ADMIN))],
) -> RecomputeResponse:
    c, t = admin_service.recompute_all(db, admin)
    return RecomputeResponse(classifications_updated=c, topper_flags_created=t)


@router.get("/users", response_model=list[AdminUserRead])
def get_users(
    db: Annotated[Session, Depends(get_db)],
    _admin: Annotated[User, Depends(require_roles(RoleName.SYSTEM_ADMIN))],
) -> list[AdminUserRead]:
    users = admin_service.list_users(db)
    return [
        AdminUserRead(
            id=u.id,
            email=u.email,
            full_name=u.full_name,
            role=u.role.name,
            is_active=u.is_active,
            created_at=u.created_at,
        )
        for u in users
    ]


@router.patch("/users/{user_id}", response_model=AdminUserRead)
def patch_user(
    user_id: uuid.UUID,
    body: AdminUserPatch,
    db: Annotated[Session, Depends(get_db)],
    admin: Annotated[User, Depends(require_roles(RoleName.SYSTEM_ADMIN))],
) -> AdminUserRead:
    u = admin_service.patch_user(db, user_id, is_active=body.is_active, role_name=body.role_name, actor=admin)
    return AdminUserRead(
        id=u.id,
        email=u.email,
        full_name=u.full_name,
        role=u.role.name,
        is_active=u.is_active,
        created_at=u.created_at,
    )


@router.get("/uploads", response_model=list[UploadMonitorItem])
def get_uploads(
    db: Annotated[Session, Depends(get_db)],
    _admin: Annotated[User, Depends(require_roles(RoleName.SYSTEM_ADMIN))],
    limit: int = 50,
    offset: int = 0,
) -> list[UploadMonitorItem]:
    rows = admin_service.list_uploads(db, limit=limit, offset=offset)
    return [
        UploadMonitorItem(
            id=r.id,
            upload_type=r.upload_type,
            file_name=r.file_name,
            status=r.status,
            row_count=r.row_count,
            success_count=r.success_count,
            error_count=r.error_count,
            uploaded_by=r.uploaded_by.full_name if r.uploaded_by else None,
            created_at=r.created_at,
            error_report_url=r.error_report_url,
        )
        for r in rows
    ]


@router.get("/uploads/{upload_id}/errors", response_model=list[UploadRowErrorRead])
def get_upload_errors(
    upload_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    _admin: Annotated[User, Depends(require_roles(RoleName.SYSTEM_ADMIN))],
) -> list[UploadRowErrorRead]:
    return admin_service.list_upload_errors(db, upload_id)


@router.post("/classification-overrides", response_model=ClassificationOverrideRead, status_code=status.HTTP_201_CREATED)
def post_override(
    body: ClassificationOverrideCreate,
    db: Annotated[Session, Depends(get_db)],
    admin: Annotated[User, Depends(require_roles(RoleName.SYSTEM_ADMIN))],
) -> ClassificationOverrideRead:
    return admin_service.create_classification_override(
        db,
        employee_id=body.employee_id,
        override_classification=body.override_classification,
        reason=body.reason,
        expires_at=body.expires_at,
        actor=admin,
    )


@router.get("/classification-overrides", response_model=list[ClassificationOverrideRead])
def get_overrides(
    db: Annotated[Session, Depends(get_db)],
    _admin: Annotated[User, Depends(require_roles(RoleName.SYSTEM_ADMIN))],
) -> list[ClassificationOverrideRead]:
    return admin_service.list_overrides(db)


@router.get("/audit-logs", response_model=list[AuditLogRead])
def get_audit_logs(
    db: Annotated[Session, Depends(get_db)],
    _admin: Annotated[User, Depends(require_roles(RoleName.SYSTEM_ADMIN))],
    limit: int = 50,
    offset: int = 0,
    action: str | None = None,
    entity_type: str | None = None,
) -> list[AuditLogRead]:
    rows, _ = audit_service.list_audit_logs(db, limit=limit, offset=offset, action=action, entity_type=entity_type)
    return rows
