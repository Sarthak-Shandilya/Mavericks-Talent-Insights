"""Human-friendly Excel column titles (row 1) for upload templates.

Ingestion normalizes headers to snake_case (spaces → underscores, lowercased), so
these labels map cleanly to internal fields without users typing snake_case.
"""

# Trainee master — one row per trainee
TRAINEE_MASTER_HEADERS: list[str] = [
    "Employee ID",
    "Superset ID",
    "Date of Joining",
    "Full Name",
    "Gender",
    "Email",
    "Phone",
    "College Name",
    "College City",
    "College State",
    "Base Location",
    "Current Training Location",
    "Training Status",
    "Stream (code)",
    "Current Training Stage (code)",
    "Category",
    "Assigned Competency",
    "Batch Code",
]

# Assessments — long format, one row per attempt
ASSESSMENTS_HEADERS: list[str] = [
    "Employee ID",
    "Program",
    "Assessment Code",
    "Attempt Number",
    "Score",
    "Max Score",
    "Assessment Date",
    "Remarks",
]

# Training stage updates
STAGES_HEADERS: list[str] = [
    "Employee ID",
    "Stage Code",
    "Status",
    "Score",
    "Attempts",
    "Completion Date",
]

# Competency rows
COMPETENCY_HEADERS: list[str] = [
    "Employee ID",
    "Competency Name",
    "Status",
    "Skill Level",
    "Readiness Flag",
    "Completion Date",
]
