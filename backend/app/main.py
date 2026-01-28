from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

load_dotenv() # Load variables from .env if it exists

from app.core.compliance import router as compliance_router
from app.routers import ingest, operations

app = FastAPI(title="CollectSecure API", version="1.0.0")

# CORS (Allow Frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"], # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "CollectSecure System Operational", "compliance_mode": "ACTIVE"}

# Include Routers
app.include_router(compliance_router, prefix="/compliance", tags=["Compliance"])
app.include_router(ingest.router, prefix="/api/v1", tags=["Ingest"])
app.include_router(operations.router, prefix="/api/v1", tags=["Operations"])
