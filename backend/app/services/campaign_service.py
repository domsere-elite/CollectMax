import json
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID
from datetime import datetime
import logging
from ..core.database import get_db_connection
from .comms import CommsManager

logger = logging.getLogger(__name__)

class CampaignService:
    def __init__(self, db_cursor):
        if db_cursor is None:
            raise ValueError("CampaignService requires a database cursor")
        self.cursor: Any = db_cursor
        self.comms = CommsManager(db_cursor)

    # ... (existing methods remain same until _build_audience_query)

    def _build_audience_query(self, filters: Dict[str, Any], count_only: bool = False) -> Tuple[str, tuple]:
        """Build SQL query for audience filtering."""
        params = []

        email_join = (
            "LEFT JOIN ("
            "SELECT DISTINCT ON (debtor_id) debtor_id, status AS last_email_status, created_at AS last_email_at "
            "FROM email_logs WHERE debtor_id IS NOT NULL ORDER BY debtor_id, created_at DESC"
            ") el ON el.debtor_id = d.id"
        )

        if count_only:
            base_query = "SELECT COUNT(DISTINCT d.id) as count FROM debtors d"
        else:
            base_query = (
                "SELECT DISTINCT ON (d.id) d.id AS debtor_id, d.email, d.first_name, d.last_name, "
                "dt.id AS debt_id, dt.amount_due, dt.status, dt.portfolio_id, el.last_email_at, el.last_email_status "
                "FROM debtors d"
            )

        joins = [
            "JOIN debts dt ON dt.debtor_id = d.id",
            email_join,
        ]

        where_clauses = [
            "d.email IS NOT NULL",
            "d.do_not_contact = FALSE",
            "d.email_unsubscribed = FALSE",
            "d.email_bounce_status IS NULL"
        ]

        # Filter: Minimum Balance
        if filters.get('min_balance') is not None and filters.get('min_balance') != "":
            where_clauses.append("dt.amount_due >= %s")
            params.append(filters['min_balance'])

        # Filter: Maximum Balance
        if filters.get('max_balance') is not None and filters.get('max_balance') != "":
            where_clauses.append("dt.amount_due <= %s")
            params.append(filters['max_balance'])
            
        # Filter: Portfolio
        if filters.get('portfolio_id') is not None and filters.get('portfolio_id') != "":
            where_clauses.append("dt.portfolio_id = %s")
            params.append(filters['portfolio_id'])

        # Filter: Debt Status (e.g., 'New', 'Open')
        if filters.get('status') is not None and filters.get('status') != "":
            where_clauses.append("dt.status = %s")
            params.append(filters['status'])

        include_unemailed = bool(filters.get('include_unemailed'))
        email_filters_present = False

        # Filter: Last Email Status
        if filters.get('last_email_status') is not None and filters.get('last_email_status') != "":
            email_filters_present = True
            if include_unemailed:
                where_clauses.append("(el.last_email_status = %s OR el.last_email_status IS NULL)")
            else:
                where_clauses.append("el.last_email_status = %s")
            params.append(filters['last_email_status'])

        # Filter: Last Email Before
        if filters.get('last_email_before') is not None and filters.get('last_email_before') != "":
            email_filters_present = True
            if include_unemailed:
                where_clauses.append("(el.last_email_at < %s OR el.last_email_at IS NULL)")
            else:
                where_clauses.append("el.last_email_at < %s")
            params.append(filters['last_email_before'])

        # Filter: Last Email After
        if filters.get('last_email_after') is not None and filters.get('last_email_after') != "":
            email_filters_present = True
            if include_unemailed:
                where_clauses.append("(el.last_email_at >= %s OR el.last_email_at IS NULL)")
            else:
                where_clauses.append("el.last_email_at >= %s")
            params.append(filters['last_email_after'])

        # Filter: Last Email Older Than (days)
        if filters.get('last_email_older_than_days') is not None and filters.get('last_email_older_than_days') != "":
            email_filters_present = True
            if include_unemailed:
                where_clauses.append("(el.last_email_at < (NOW() - make_interval(days => %s)) OR el.last_email_at IS NULL)")
            else:
                where_clauses.append("el.last_email_at < (NOW() - make_interval(days => %s))")
            params.append(filters['last_email_older_than_days'])

        if include_unemailed and not email_filters_present:
            where_clauses.append("el.last_email_at IS NULL")

        if count_only:
            query = f"{base_query} {' '.join(joins)} WHERE {' AND '.join(where_clauses)}"
        else:
            query = (
                f"{base_query} {' '.join(joins)} WHERE {' AND '.join(where_clauses)} "
                "ORDER BY d.id, dt.id"
            )

        return query, tuple(params)


    def get_templates(self) -> List[Dict[str, Any]]:
        """List all registered email templates."""
        self.cursor.execute("SELECT * FROM email_templates ORDER BY name")
        return self.cursor.fetchall()

    def register_template(self, name: str, template_id: str, description: str = "") -> Dict[str, Any]:
        """Register a SendGrid template in the system."""
        try:
            desc_value = description if description else None
            self.cursor.execute("""
                INSERT INTO email_templates (name, template_id, description)
                VALUES (%s, %s, %s)
                RETURNING *
            """, (name, template_id, desc_value))
            return self.cursor.fetchone()
        except Exception as e:
            logger.error(f"Error registering template: {e}")
            raise

    def estimate_audience(self, filters: Dict[str, Any]) -> int:
        """Count how many debtors match the filters."""
        query, params = self._build_audience_query(filters, count_only=True)
        self.cursor.execute(query, params)
        return self.cursor.fetchone()['count']

    def create_campaign(self, name: str, subject: str, template_id: str, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new campaign and populate recipients."""
        try:
            # 1. Create Campaign Record
            self.cursor.execute("""
                INSERT INTO campaigns (name, subject, template_id, filters, status)
                VALUES (%s, %s, %s, %s, 'draft')
                RETURNING id
            """, (name, subject, template_id, json.dumps(filters)))
            campaign_id = self.cursor.fetchone()['id']

            # 2. Insert Recipients from Audience
            query, params = self._build_audience_query(filters, count_only=False)
            insert_sql = (
                "INSERT INTO campaign_recipients (campaign_id, debtor_id, debt_id, email_to) "
                "SELECT %s, debtor_id, debt_id, email FROM (" + query + ") audience"
            )
            self.cursor.execute(insert_sql, (campaign_id, *params))

            # 3. Update total count
            self.cursor.execute("SELECT COUNT(*) AS count FROM campaign_recipients WHERE campaign_id = %s", (campaign_id,))
            count = self.cursor.fetchone()['count']
            self.cursor.execute("UPDATE campaigns SET total_recipients = %s WHERE id = %s", (count, campaign_id))

            return {"id": campaign_id, "recipient_count": count}

        except Exception as e:
            logger.error(f"Error creating campaign: {e}")
            raise

    def launch_campaign(self, campaign_id: int):
        """
        Execute a campaign: iterate recipients and send emails.
        In production, this should be a background task (Celery/APScheduler).
        """
        try:
            # 1. Update status to sending
            self.cursor.execute("UPDATE campaigns SET status = 'sending', sent_at = NOW() WHERE id = %s", (campaign_id,))
            
            # 2. Get Template ID
            self.cursor.execute("SELECT template_id, subject FROM campaigns WHERE id = %s", (campaign_id,))
            campaign = self.cursor.fetchone()
            if not campaign:
                raise ValueError("Campaign not found")
            template_id = campaign['template_id']
            subject = campaign['subject']

            # 3. Get Pending Recipients
            self.cursor.execute("""
                SELECT cr.id, cr.email_to, cr.debtor_id, d.first_name, d.last_name, 
                       dt.amount_due, dt.id as debt_id,
                       dt.client_reference_number, dt.original_account_number, 
                       dt.original_creditor, dt.current_creditor, dt.charge_off_date,
                       c.name as current_creditor_name,
                       d.address_1, d.city, d.state, d.zip_code
                FROM campaign_recipients cr
                JOIN debtors d ON cr.debtor_id = d.id
                LEFT JOIN debts dt ON dt.id = cr.debt_id
                LEFT JOIN portfolios p ON dt.portfolio_id = p.id
                LEFT JOIN clients c ON p.client_id = c.id
                WHERE cr.campaign_id = %s AND cr.status = 'pending'
            """, (campaign_id,))
            
            recipients = self.cursor.fetchall()
            
            sent_count = 0
            failed_count = 0
            
            from datetime import timedelta
            today = datetime.now()
            today_str = today.strftime("%B %d, %Y")
            date_plus_30_str = (today + timedelta(days=30)).strftime("%B %d, %Y")

            for r in recipients:
                # Format Charge Off Date
                co_date = r['charge_off_date'].strftime("%B %d, %Y") if r['charge_off_date'] else "N/A"

                # Dynamic Data for SendGrid
                dynamic_data = {
                    "first_name": r['first_name'],
                    "last_name": r['last_name'],
                    "balance": f"{float(r['amount_due']):,.2f}" if r['amount_due'] else "0.00",
                    "consumer_id": r['client_reference_number'] or "N/A",
                    "original_account_number": r['original_account_number'],
                    "original_creditor": r['original_creditor'] or "Unknown Creditor",
                    "current_creditor": r.get('current_creditor') or r.get('current_creditor_name') or "Elite Portfolio Management",
                    "charge_off_date": co_date,
                    "today_date": today_str,
                    "date_plus_30": date_plus_30_str,
                    "issuer": r['original_creditor'] or "Unknown Issuer",
                    "address_line_1": r['address_1'] or "",
                    "city": r['city'] or "",
                    "state": r['state'] or "",
                    "zip_code": r['zip_code'] or "",
                    "email_address": r['email_to'],
                    "unsubscribe_link": "<%asm_group_unsubscribe_url%>"
                }
                
                # Send Email via CommsManager
                result = self.comms.send_email(
                    to_email=r['email_to'],
                    subject=subject,
                    html_content="", # Template used
                    debt_id=r['debt_id'], # Log against first debt
                    template_id=template_id,
                    dynamic_data=dynamic_data
                )
                
                # Update Recipient Status
                new_status = 'sent' if result['success'] else 'failed'
                error_msg = result.get('error')
                sg_msg_id = result.get('message_id')
                
                self.cursor.execute("""
                    UPDATE campaign_recipients 
                    SET status = %s, sendgrid_message_id = %s, error_message = %s, sent_at = NOW()
                    WHERE id = %s
                """, (new_status, sg_msg_id, error_msg, r['id']))
                
                if result['success']:
                    sent_count += 1
                else:
                    failed_count += 1
            
            # 4. Update Campaign Stats
            self.cursor.execute("""
                UPDATE campaigns 
                SET status = 'completed', sent_count = %s, failed_count = %s
                WHERE id = %s
            """, (sent_count, failed_count, campaign_id))
            
            return {"status": "completed", "sent": sent_count, "failed": failed_count}

        except Exception as e:
            logger.error(f"Error launching campaign {campaign_id}: {e}")
            self.cursor.execute("UPDATE campaigns SET status = 'failed' WHERE id = %s", (campaign_id,))
            raise

    def list_campaigns(self) -> List[Dict[str, Any]]:
        """List campaigns with rollup metrics."""
        self.cursor.execute("""
            SELECT c.*, 
                   (SELECT COUNT(*) FROM campaign_recipients cr WHERE cr.campaign_id = c.id AND cr.status = 'sent') AS sent_count,
                   (SELECT COUNT(*) FROM campaign_recipients cr WHERE cr.campaign_id = c.id AND cr.status = 'failed') AS failed_count,
                   (SELECT COUNT(*) FROM campaign_recipients cr 
                    JOIN email_logs el ON el.sendgrid_message_id = cr.sendgrid_message_id
                    WHERE cr.campaign_id = c.id AND el.status IN ('delivered','opened','clicked')) AS delivered_count,
                   (SELECT COUNT(*) FROM campaign_recipients cr 
                    JOIN email_logs el ON el.sendgrid_message_id = cr.sendgrid_message_id
                    WHERE cr.campaign_id = c.id AND el.status = 'opened') AS opened_count,
                   (SELECT COUNT(*) FROM campaign_recipients cr 
                    JOIN email_logs el ON el.sendgrid_message_id = cr.sendgrid_message_id
                    WHERE cr.campaign_id = c.id AND el.status = 'clicked') AS clicked_count
            FROM campaigns c
            ORDER BY c.created_at DESC
        """)
        return self.cursor.fetchall()
