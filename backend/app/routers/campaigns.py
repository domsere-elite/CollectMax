from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from psycopg2.extras import RealDictCursor
from ..core.database import get_db, get_db_connection
from ..services.campaign_service import CampaignService

router = APIRouter(prefix="/campaigns", tags=["Campaigns"])

# --- Pydantic Models ---
class TemplateCreate(BaseModel):
    name: str
    template_id: str
    description: Optional[str] = None

class CampaignFilter(BaseModel):
    min_balance: Optional[float] = None
    max_balance: Optional[float] = None
    portfolio_id: Optional[int] = None
    status: Optional[str] = None
    last_email_status: Optional[str] = None
    last_email_before: Optional[str] = None
    last_email_after: Optional[str] = None
    last_email_older_than_days: Optional[int] = None
    include_unemailed: Optional[bool] = False

class CampaignCreate(BaseModel):
    name: str
    subject: str
    template_id: str
    filters: CampaignFilter

class CampaignPreview(BaseModel):
    recipient_count: int

# --- Endpoints ---

@router.get("/templates")
def list_templates(db=Depends(get_db)):
    cursor = db.cursor(cursor_factory=RealDictCursor)
    service = CampaignService(cursor)
    try:
        return service.get_templates()
    finally:
        cursor.close()

@router.post("/templates")
def register_template(template: TemplateCreate, db=Depends(get_db)):
    cursor = db.cursor(cursor_factory=RealDictCursor)
    service = CampaignService(cursor)
    try:
        result = service.register_template(template.name, template.template_id, str(template.description or ""))
        db.commit()
        return result
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()

@router.post("/preview", response_model=CampaignPreview)
def preview_audience(filters: CampaignFilter, db=Depends(get_db)):
    cursor = db.cursor(cursor_factory=RealDictCursor)
    service = CampaignService(cursor)
    try:
        count = service.estimate_audience(filters.dict(exclude_none=True))
        return {"recipient_count": count}
    finally:
        cursor.close()

@router.post("/launch")
def launch_campaign(
    campaign: CampaignCreate, 
    background_tasks: BackgroundTasks,
    db=Depends(get_db)
):
    """
    Creates a campaign and triggers background sending.
    """
    cursor = db.cursor(cursor_factory=RealDictCursor)
    service = CampaignService(cursor)
    try:
        # Create Campaign & Recipients
        result = service.create_campaign(
            name=campaign.name,
            subject=campaign.subject,
            template_id=campaign.template_id,
            filters=campaign.filters.dict(exclude_none=True)
        )
        db.commit()
        
        # Trigger Background Sending
        background_tasks.add_task(run_campaign_task_bg, result['id'])
        
        return {
            "status": "queued",
            "campaign_id": result['id'],
            "recipient_count": result['recipient_count']
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()


@router.get("")
def list_campaigns(db=Depends(get_db)):
    cursor = db.cursor(cursor_factory=RealDictCursor)
    service = CampaignService(cursor)
    try:
        return service.list_campaigns()
    finally:
        cursor.close()

# --- Background Task Helper ---

def run_campaign_task_bg(campaign_id: int):
    """
    Standalone background task to run the campaign.
    Creates its own DB connection.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        service = CampaignService(cursor)
        
        service.launch_campaign(campaign_id)
        
        conn.commit()
    except Exception as e:
        print(f"Background Campaign Error: {e}")
        conn.rollback() # Important!
    finally:
        conn.close()
