from fastapi import APIRouter, Request, HTTPException, Depends
from typing import List, Dict, Any
import json
from psycopg2.extras import Json
import logging
from datetime import datetime
from ..core.database import get_db

router = APIRouter(prefix="/webhooks", tags=["webhooks"])
logger = logging.getLogger(__name__)


@router.post("/sendgrid")
async def sendgrid_webhook(request: Request, db=Depends(get_db)):
    """
    Handle SendGrid webhook events for email tracking.
    
    Events include: delivered, opened, clicked, bounced, dropped, spam_report, unsubscribe
    
    SendGrid webhook documentation:
    https://docs.sendgrid.com/for-developers/tracking-events/event
    """
    cursor = db.cursor()
    
    try:
        # Parse webhook payload
        events: List[Dict[str, Any]] = await request.json()
        
        for event in events:
            event_type = event.get('event')
            sg_message_id = event.get('sg_message_id')
            email = event.get('email')
            timestamp = event.get('timestamp')
            
            if not sg_message_id:
                logger.warning(f"Received event without sg_message_id: {event_type}")
                continue

            sg_message_id_base = sg_message_id.split(".")[0] if "." in sg_message_id else sg_message_id
            
            # Convert Unix timestamp to datetime
            event_time = datetime.fromtimestamp(timestamp) if timestamp else None
            
            # Update email_logs based on event type
            if event_type == 'delivered':
                cursor.execute("""
                    UPDATE email_logs 
                    SET status = 'delivered', delivered_at = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE sendgrid_message_id = %s OR sendgrid_message_id = %s
                """, (event_time, sg_message_id, sg_message_id_base))
                
            elif event_type == 'open':
                cursor.execute("""
                    UPDATE email_logs 
                    SET status = 'opened', opened_at = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE sendgrid_message_id = %s OR sendgrid_message_id = %s
                """, (event_time, sg_message_id, sg_message_id_base))
                
            elif event_type == 'click':
                cursor.execute("""
                    UPDATE email_logs 
                    SET status = 'clicked', clicked_at = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE sendgrid_message_id = %s OR sendgrid_message_id = %s
                """, (event_time, sg_message_id, sg_message_id_base))
                
            elif event_type in ['bounce', 'dropped']:
                bounce_reason = event.get('reason', '')
                bounce_type = event.get('type', 'unknown')  # hard or soft bounce
                
                cursor.execute("""
                    UPDATE email_logs 
                    SET status = 'bounced', bounced_at = %s, bounce_reason = %s, 
                        updated_at = CURRENT_TIMESTAMP
                    WHERE sendgrid_message_id = %s OR sendgrid_message_id = %s
                """, (event_time, bounce_reason, sg_message_id, sg_message_id_base))
                
                # Update debtor bounce status for hard bounces
                if bounce_type == 'hard':
                    cursor.execute("""
                        UPDATE debtors 
                        SET email_bounce_status = 'hard_bounce',
                            email_last_bounced_at = %s
                        WHERE email = %s
                    """, (event_time, email))
                    
            elif event_type == 'spam_report':
                cursor.execute("""
                    UPDATE email_logs 
                    SET status = 'spam', updated_at = CURRENT_TIMESTAMP
                    WHERE sendgrid_message_id = %s OR sendgrid_message_id = %s
                """, (sg_message_id, sg_message_id_base))
                
                # Mark debtor as unsubscribed
                cursor.execute("""
                    UPDATE debtors 
                    SET email_unsubscribed = TRUE,
                        email_unsubscribed_at = %s,
                        email_bounce_status = 'spam'
                    WHERE email = %s
                """, (event_time, email))
                
            elif event_type == 'unsubscribe':
                cursor.execute("""
                    UPDATE debtors 
                    SET email_unsubscribed = TRUE,
                        email_unsubscribed_at = %s
                    WHERE email = %s
                """, (event_time, email))
            
            # Store full event metadata in JSONB field
            cursor.execute("""
                UPDATE email_logs 
                SET metadata = %s
                WHERE sendgrid_message_id = %s OR sendgrid_message_id = %s
            """, (Json(event), sg_message_id, sg_message_id_base))
        
        db.commit()
        logger.info(f"Processed {len(events)} SendGrid webhook events")
        
        return {"status": "success", "processed": len(events)}
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error processing SendGrid webhook: {str(e)}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")
    
    finally:
        cursor.close()


@router.get("/sendgrid/test")
def test_webhook():
    """
    Test endpoint to verify webhook is accessible.
    """
    return {
        "status": "ok",
        "message": "SendGrid webhook endpoint is active",
        "endpoint": "/api/webhooks/sendgrid"
    }
