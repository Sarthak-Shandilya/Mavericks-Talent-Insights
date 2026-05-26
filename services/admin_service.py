"""System admin operations."""
from __future__ import annotations

import uuid
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session, joinedload

from models.automation import ClassificationOverride, ScoringConfig, TopperRule
from models.trainee import Trainee
from models.upload_audit import UploadBatch, UploadRowError
from models.user import User
import repositories.role_repository as role_repository
import repositories.user_repository as user_repository
from services import audit_service
from services.scoring_service import classify_trainee, recompute_all_classifications
from services.topper_service import recompute_all_toppers


def list_scoring_configs(db: Session) -> list[ScoringConfig]:
    return list(db.execute(select(ScoringConfig).order_by(ScoringConfig.version.desc())).scalars().all())


def create_scoring_config(db: Session, *, weights: dict, high_threshold: Decimal, average_threshold: Decimal, actor: User) -> ScoringConfig:
    max_ver = db.execute(select(func.max(ScoringConfig.version))).scalar() or 0
    config = ScoringConfig(
        version=max_ver + 1,
        is_active=False,
        weights=weights,
        high_threshold=high_threshold,
        average_threshold=average_threshold,
        created_by_user_id=actor.id,
    )
    db.add(config)
    db.commit()
    db.refresh(config)
    audit_service.log_action(db, actor=actor, action="scoring_config.create", entity_type="scoring_config", entity_id=config.id, details={"version": config.version})
    db.commit()
    return config


def activate_scoring_config(db: Session, config_id: uuid.UUID, actor: User) -> ScoringConfig:
    config = db.get(ScoringConfig, config_id)
    if not config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scoring config not found")
    db.execute(update(ScoringConfig).values(is_active=False))
    config.is_active = True
    db.commit()
    db.refresh(config)
    audit_service.log_action(db, actor=actor, action="scoring_config.activate", entity_type="scoring_config", entity_id=config.id)
    db.commit()
    recompute_all_classifications(db)
    db.commit()
    return config


def list_topper_rules(db: Session) -> list[TopperRule]:
    return list(db.execute(select(TopperRule).order_by(TopperRule.topper_type)).scalars().all())


def create_topper_rule(db: Session, data: dict, actor: User) -> TopperRule:
    rule = TopperRule(**data, version=1)
    db.add(rule)
    db.commit()
    db.refresh(rule)
    audit_service.log_action(db, actor=actor, action="topper_rule.create", entity_type="topper_rule", entity_id=rule.id)
    db.commit()
    return rule


def update_topper_rule(db: Session, rule_id: uuid.UUID, updates: dict, actor: User) -> TopperRule:
    rule = db.get(TopperRule, rule_id)
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topper rule not found")
    for k, v in updates.items():
        if v is not None and hasattr(rule, k):
            setattr(rule, k, v)
    db.commit()
    db.refresh(rule)
    audit_service.log_action(db, actor=actor, action="topper_rule.update", entity_type="topper_rule", entity_id=rule.id, details=updates)
    db.commit()
    return rule


def delete_topper_rule(db: Session, rule_id: uuid.UUID, actor: User) -> None:
    rule = db.get(TopperRule, rule_id)
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topper rule not found")
    rule.is_active = False
    db.commit()
    audit_service.log_action(db, actor=actor, action="topper_rule.deactivate", entity_type="topper_rule", entity_id=rule_id)
    db.commit()


def create_classification_override(db: Session, *, employee_id: str, override_classification: str, reason: str | None, expires_at, actor: User):
    trainee = db.execute(select(Trainee).where(Trainee.employee_id == employee_id)).scalar_one_or_none()
    if not trainee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trainee not found")
    override = ClassificationOverride(
        trainee_id=trainee.id,
        override_classification=override_classification,
        reason=reason,
        created_by_user_id=actor.id,
        expires_at=expires_at,
    )
    db.add(override)
    db.commit()
    classify_trainee(db, trainee.id)
    db.commit()
    audit_service.log_action(db, actor=actor, action="classification.override", entity_type="trainee", entity_id=trainee.id, details={"band": override_classification})
    db.commit()
    return override


def list_overrides(db: Session, limit: int = 50) -> list[ClassificationOverride]:
    return list(db.execute(select(ClassificationOverride).order_by(ClassificationOverride.created_at.desc()).limit(limit)).scalars().all())


def list_users(db: Session) -> list[User]:
    return list(db.execute(select(User).options(joinedload(User.role))).unique().scalars().all())


def patch_user(db: Session, user_id: uuid.UUID, *, is_active: bool | None, role_name: str | None, actor: User) -> User:
    user = user_repository.get_by_id_with_role(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if is_active is not None:
        user.is_active = is_active
    if role_name:
        role = role_repository.get_by_name(db, role_name)
        if not role:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role")
        user.role_id = role.id
    db.commit()
    db.refresh(user)
    audit_service.log_action(db, actor=actor, action="user.update", entity_type="user", entity_id=user.id)
    db.commit()
    return user_repository.get_by_id_with_role(db, user_id)


def list_uploads(db: Session, limit: int = 50, offset: int = 0) -> list[UploadBatch]:
    return list(
        db.execute(
            select(UploadBatch)
            .options(joinedload(UploadBatch.uploaded_by))
            .order_by(UploadBatch.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        .unique()
        .scalars()
        .all()
    )


def list_upload_errors(db: Session, upload_id: uuid.UUID) -> list[UploadRowError]:
    return list(db.execute(select(UploadRowError).where(UploadRowError.upload_id == upload_id)).scalars().all())


def recompute_all(db: Session, actor: User) -> tuple[int, int]:
    c = recompute_all_classifications(db)
    t = recompute_all_toppers(db)
    db.commit()
    audit_service.log_action(db, actor=actor, action="automation.recompute", entity_type="system", details={"classifications": c, "toppers": t})
    db.commit()
    return c, t
