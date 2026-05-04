from enum import StrEnum


class TrainingStatus(StrEnum):
    ACTIVE = "ACTIVE"
    ON_HOLD = "ON_HOLD"
    COMPLETED = "COMPLETED"
    DROPPED = "DROPPED"


class StageRowStatus(StrEnum):
    COMPLETED = "COMPLETED"
    PENDING = "PENDING"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class AssessmentProgram(StrEnum):
    SPARK = "SPARK"
    FOUNDATION = "FOUNDATION"
    TECHNICAL = "TECHNICAL"
    PROJECT = "PROJECT"
    SOFT_SKILL = "SOFT_SKILL"
    CODING_TEST = "CODING_TEST"


class CompetencyStatus(StrEnum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


class SkillLevel(StrEnum):
    BEGINNER = "BEGINNER"
    INTERMEDIATE = "INTERMEDIATE"
    ADVANCED = "ADVANCED"
    EXPERT = "EXPERT"


class PerformanceBand(StrEnum):
    HIGH = "HIGH"
    AVERAGE = "AVERAGE"
    LOW = "LOW"


class UploadType(StrEnum):
    TRAINEE_MASTER = "TRAINEE_MASTER"
    ASSESSMENTS = "ASSESSMENTS"
    STAGES = "STAGES"
    COMPETENCY = "COMPETENCY"


class UploadStatus(StrEnum):
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class TopperType(StrEnum):
    SPARK = "SPARK"
    FOUNDATION = "FOUNDATION"
    STREAM = "STREAM"
    BATCH = "BATCH"
    COMPETENCY = "COMPETENCY"
