from fastapi import APIRouter, UploadFile, File, BackgroundTasks, Form, HTTPException
import os
import shutil
import uuid
from app.services.ingest import run_ingest_job
from app.core.database import get_db_connection

router = APIRouter()

@router.post("/upload")
async def upload_portfolio(
    file: UploadFile = File(...),
    portfolio_id: int = Form(1),
    background_tasks: BackgroundTasks = None
):
    """
    Accepts a CSV file upload and processes it in the background.
    Returns a job id for status tracking.
    """
    try:
        upload_dir = os.path.join(os.getcwd(), "backend", "uploads")
        os.makedirs(upload_dir, exist_ok=True)

        # Persist upload to disk for background processing
        safe_name = file.filename or "upload.csv"
        base, ext = os.path.splitext(safe_name)
        job_file_name = f"{base}_{uuid.uuid4().hex}{ext or '.csv'}"
        job_file_path = os.path.join(upload_dir, job_file_name)

        with open(job_file_path, "wb") as out_file:
            file.file.seek(0)
            shutil.copyfileobj(file.file, out_file)

        # Create ingest job record
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                """
                INSERT INTO ingest_jobs (portfolio_id, filename, file_path, status)
                VALUES (%s, %s, %s, 'queued')
                RETURNING id
                """,
                (portfolio_id, safe_name, job_file_path)
            )
            job_id = cur.fetchone()[0]
            conn.commit()
        finally:
            cur.close()
            conn.close()

        if background_tasks is None:
            raise HTTPException(status_code=500, detail="Background task system not available")

        background_tasks.add_task(run_ingest_job, str(job_id), job_file_path, portfolio_id)
        return {"status": "Queued", "filename": safe_name, "job_id": str(job_id)}
    except Exception as e:
        return {"status": "Error", "filename": file.filename, "error": str(e)}


@router.get("/ingest/jobs/{job_id}")
def get_ingest_job(job_id: str):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT id, status, portfolio_id, filename, rows_processed, rows_failed,
                   error_message, created_at, started_at, finished_at
            FROM ingest_jobs
            WHERE id = %s
            """,
            (job_id,)
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Ingest job not found")

        return {
            "id": str(row[0]),
            "status": row[1],
            "portfolio_id": row[2],
            "filename": row[3],
            "rows_processed": row[4],
            "rows_failed": row[5],
            "error_message": row[6],
            "created_at": row[7],
            "started_at": row[8],
            "finished_at": row[9],
        }
    finally:
        cur.close()
        conn.close()
