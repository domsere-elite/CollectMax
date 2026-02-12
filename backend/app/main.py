from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
from zoneinfo import ZoneInfo
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

load_dotenv() # Load variables from .env if it exists

from app.core.compliance import router as compliance_router
from app.routers import ingest, operations, webhooks, campaigns
from app.core.auth import require_auth
from app.services.scheduled_runner import run_due_scheduled_payments

app = FastAPI(title="CollectSecure API", version="1.0.0")
scheduler = None

# CORS (Allow Frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(","),
    # allow_origin_regex=r"^http://(localhost|127\.0\.0\.1)(:\\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def start_scheduler():
    global scheduler
    if os.getenv("ENABLE_SCHEDULER", "false").lower() != "true":
        return

    scheduler = BackgroundScheduler(timezone=ZoneInfo("America/Chicago"))
    scheduler.add_job(run_due_scheduled_payments, CronTrigger(hour=5, minute=0), args=["am"])
    scheduler.add_job(run_due_scheduled_payments, CronTrigger(hour=17, minute=0), args=["pm"])
    scheduler.start()


@app.on_event("shutdown")
def stop_scheduler():
    if scheduler:
        scheduler.shutdown()

@app.get("/")
def read_root():
    return {"status": "CollectSecure System Operational", "compliance_mode": "ACTIVE"}



# Include Routers
app.include_router(compliance_router, prefix="/compliance", tags=["Compliance"])
app.include_router(ingest.router, prefix="/api/v1", tags=["Ingest"], dependencies=[Depends(require_auth)])
app.include_router(operations.router, prefix="/api/v1", tags=["Operations"], dependencies=[Depends(require_auth)])
app.include_router(webhooks.router, prefix="/api", tags=["Webhooks"])
app.include_router(campaigns.router, prefix="/api/v1", tags=["Campaigns"], dependencies=[Depends(require_auth)])
