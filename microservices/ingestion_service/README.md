# Ingestion Service

Independent worker for Excel ingestion. It consumes queue messages, downloads files from configured storage, validates rows, writes errors to `upload_row_errors`, and performs 1000-row UPSERT batches into shared PostgreSQL.

## Run

1. Copy `.env.example` to `.env`
2. Install dependencies from `requirements.txt`
3. Run `python main.py`
