"""App-wide constants (e.g. RBAC role names matching seeded `roles.name`)."""

from enum import StrEnum


class RoleName(StrEnum):
    TRAINING_COORDINATOR = "training_coordinator"
    TRAINER = "trainer"
    HR = "hr"
    BUSINESS_HEAD = "business_head"
    SYSTEM_ADMIN = "system_admin"
