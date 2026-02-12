import csv
import hashlib
import os
from datetime import timezone
import re
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Dict, Any

from psycopg2.extras import execute_values

class CSVImporter:
    def __init__(self, file_obj):
        self.file_obj = file_obj

    HEADER_MAPPING = {
        'PSSN_SIN': 'ssn',
        'PFName': 'first_name',
        'PLName': 'last_name',
        'PBirthdate': 'date_of_birth',
        '1stAddress1': 'address_line_1',
        '1stAddress2': 'address_line_2',
        '1stCity': 'city',
        '1stState': 'state',
        '1stZipPostal': 'zip_code',
        '1stPhone': 'primary_phone',
        'PEmail': 'email_address',
        'IssuerAccountNumber': 'original_account',
        'ClientAccountID': 'client_reference',
        'IssuerName': 'original_creditor',
        'CurrentCreditor': 'current_creditor',
        'CurrentCreditorName': 'current_creditor',
        'Current Creditor': 'current_creditor',
        'AccountOpenDate': 'date_opened',
        'CODate': 'charge_off_date',
        'Principal': 'principal_balance',
        'Orig_FeeBalance': 'fees_costs',
        'CurBalance': 'total_placed',
        'LastPayDate': 'last_payment_date',
        'LastPayAmount': 'last_payment_amt',
        # Fallback for standard headers if they happen to match exactly
        'SSN': 'ssn',
        'First Name': 'first_name',
        'Last Name': 'last_name'
    }

    def normalize_header(self, header: str) -> str:
        """
        Maps client header to internal schema using HEADER_MAPPING.
        Falls back to snake_case if no map found.
        """
        # Exact match lookup
        if header in self.HEADER_MAPPING:
            return self.HEADER_MAPPING[header]
            
        # Fallback normalization
        clean = header.replace('#', '').replace('*', '').strip()
        return clean.lower().replace(' ', '_').replace('/', '_')

    def parse_date(self, date_str: str):
        """
        Attempts MM/DD/YYYY and YYYY-MM-DD. Returns None if invalid or empty.
        """
        if not date_str:
            return None
        for fmt in ('%m/%d/%Y', '%Y-%m-%d'):
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        return None # Log error in real app

    def sanitize_phone(self, phone: str):
        if not phone:
            return None
        return re.sub(r'[()\-\s]', '', phone)

    def hash_ssn(self, ssn: str, fallback_seed: str = ""):
        """
        Hash SSN when present; otherwise use a deterministic fallback
        to avoid collapsing all missing-SSN debtors into a single record.
        """
        if ssn:
            return hashlib.sha256(ssn.encode()).hexdigest()
        if not fallback_seed:
            fallback_seed = "unknown"
        return hashlib.sha256(fallback_seed.encode()).hexdigest()

    def clean_decimal(self, value):
        if not value:
            return Decimal("0.00")
        return Decimal(value.replace('$', '').replace(',', ''))

    def process(self, portfolio_id: int, batch_size: int = 1000, progress_cb=None):
        """
        Main entry point. Returns stats.
        """
        rows_processed = 0
        reader = csv.DictReader(self.file_obj)

        if os.getenv("ENABLE_INGEST_DEBUG", "false").lower() == "true":
            with open("ingest_debug.log", "w") as f:
                f.write(f"Detected Headers: {reader.fieldnames}\n")

        conn = self.get_db()
        try:
            batch: List[Dict[str, Any]] = []
            for row in reader:
                if rows_processed == 0 and os.getenv("ENABLE_INGEST_DEBUG", "false").lower() == "true":
                    with open("ingest_debug.log", "a") as f:
                        f.write(f"First Row Raw: {row}\n")

                clean_row = {self.normalize_header(k): v for k, v in row.items()}
                if rows_processed == 0 and os.getenv("ENABLE_INGEST_DEBUG", "false").lower() == "true":
                    with open("ingest_debug.log", "a") as f:
                        f.write(f"First Row Cleaned: {clean_row}\n")

                batch.append(clean_row)
                rows_processed += 1

                if len(batch) >= batch_size:
                    self.process_batch(conn, batch, portfolio_id)
                    if progress_cb:
                        progress_cb(rows_processed)
                    batch = []

            if batch:
                self.process_batch(conn, batch, portfolio_id)
                if progress_cb:
                    progress_cb(rows_processed)
        finally:
            conn.close()

        return rows_processed

    def process_batch(self, conn, rows: List[Dict[str, Any]], portfolio_id: int):
        """
        Process a batch of rows using a single DB connection.
        """
        cursor = conn.cursor()
        try:
            debtor_rows = []
            ssn_hashes = []

            for row in rows:
                phone = self.sanitize_phone(row.get('primary_phone'))
                zip_5 = (row.get('zip_code') or '')[:5]
                dob = self.parse_date(row.get('date_of_birth'))

                fallback_seed = "|".join([
                    (row.get('first_name') or '').strip().lower(),
                    (row.get('last_name') or '').strip().lower(),
                    str(dob or ''),
                    zip_5
                ])
                ssn_hash = self.hash_ssn(row.get('ssn'), fallback_seed)

                debtor_rows.append({
                    "ssn_hash": ssn_hash,
                    "first_name": row.get('first_name'),
                    "last_name": row.get('last_name'),
                    "dob": dob,
                    "address_1": row.get('address_line_1'),
                    "address_2": row.get('address_line_2'),
                    "city": row.get('city'),
                    "state": row.get('state'),
                    "zip_code": zip_5,
                    "phone": phone,
                    "mobile_consent": (row.get('mobile_consent', 'False') or '').lower() == 'true',
                    "email": row.get('email_address')
                })
                ssn_hashes.append(ssn_hash)

            # 1) Load existing debtors
            cursor.execute(
                "SELECT id, ssn_hash FROM debtors WHERE ssn_hash = ANY(%s)",
                (ssn_hashes,)
            )
            existing = cursor.fetchall()
            debtor_map = {row[1]: row[0] for row in existing}

            # 2) Insert missing debtors
            missing_map = {}
            for d in debtor_rows:
                if d["ssn_hash"] not in debtor_map and d["ssn_hash"] not in missing_map:
                    missing_map[d["ssn_hash"]] = d

            if missing_map:
                values = [
                    (
                        d["ssn_hash"], d["first_name"], d["last_name"], d["dob"],
                        d["address_1"], d["address_2"], d["city"], d["state"],
                        d["zip_code"], d["phone"], d["mobile_consent"], d["email"]
                    )
                    for d in missing_map.values()
                ]
                execute_values(
                    cursor,
                    """
                    INSERT INTO debtors (
                        ssn_hash, first_name, last_name, dob, address_1, address_2,
                        city, state, zip_code, phone, mobile_consent, email
                    ) VALUES %s
                    ON CONFLICT (ssn_hash) DO NOTHING
                    RETURNING id, ssn_hash
                    """,
                    values
                )
                inserted = cursor.fetchall()
                for row in inserted:
                    debtor_map[row[1]] = row[0]

                # Ensure any concurrent inserts are picked up
                cursor.execute(
                    "SELECT id, ssn_hash FROM debtors WHERE ssn_hash = ANY(%s)",
                    (list(missing_map.keys()),)
                )
                refreshed = cursor.fetchall()
                for row in refreshed:
                    debtor_map[row[1]] = row[0]

            # 3) Insert debts for all rows
            debt_values = []
            for row, debtor in zip(rows, debtor_rows):
                debt_values.append((
                    str(debtor_map[debtor["ssn_hash"]]),
                    portfolio_id,
                    row.get('client_reference'),
                    row.get('original_account'),
                    row.get('original_creditor'),
                    row.get('current_creditor') or row.get('original_creditor'),
                    self.parse_date(row.get('date_opened')),
                    self.parse_date(row.get('charge_off_date')),
                    self.clean_decimal(row.get('principal_balance')),
                    self.clean_decimal(row.get('fees_costs')),
                    self.clean_decimal(row.get('total_placed')),
                    self.clean_decimal(row.get('total_placed')),
                    self.parse_date(row.get('last_payment_date')),
                    self.clean_decimal(row.get('last_payment_amt')),
                ))

            execute_values(
                cursor,
                """
                INSERT INTO debts (
                    debtor_id, portfolio_id, client_reference_number, original_account_number,
                    original_creditor, current_creditor, date_opened, charge_off_date, principal_balance,
                    fees_costs, face_value, amount_due, last_payment_date, last_payment_amount, status
                ) VALUES %s
                ON CONFLICT (portfolio_id, client_reference_number)
                WHERE client_reference_number IS NOT NULL
                DO NOTHING
                """,
                debt_values,
                template="(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'New')"
            )

            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"Error processing batch: {e}")
            raise e
        finally:
            cursor.close()

    def get_db(self):
        from app.core.database import get_db_connection
        return get_db_connection()


def _update_job_status(job_id: str, **fields):
    from app.core.database import get_db_connection
    if not fields:
        return
    set_parts = []
    values = []
    for key, value in fields.items():
        set_parts.append(f"{key} = %s")
        values.append(value)
    values.append(job_id)
    sql = f"UPDATE ingest_jobs SET {', '.join(set_parts)} WHERE id = %s"
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(sql, tuple(values))
        conn.commit()
    finally:
        cur.close()
        conn.close()


def run_ingest_job(job_id: str, file_path: str, portfolio_id: int, batch_size: int = 1000):
    """
    Background job runner for CSV ingestion.
    """
    env_batch = os.getenv("INGEST_BATCH_SIZE")
    if env_batch and env_batch.isdigit():
        batch_size = int(env_batch)
    started_at = datetime.now(timezone.utc)
    _update_job_status(job_id, status="running", started_at=started_at, error_message=None, rows_processed=0, rows_failed=0)

    try:
        with open(file_path, "r", encoding="utf-8", newline="") as f:
            importer = CSVImporter(f)

            def progress_cb(count):
                _update_job_status(job_id, rows_processed=count)

            rows = importer.process(portfolio_id=portfolio_id, batch_size=batch_size, progress_cb=progress_cb)

        finished_at = datetime.now(timezone.utc)
        _update_job_status(job_id, status="completed", finished_at=finished_at, rows_processed=rows)
    except Exception as e:
        finished_at = datetime.now(timezone.utc)
        _update_job_status(job_id, status="failed", finished_at=finished_at, error_message=str(e))
    finally:
        if os.getenv("INGEST_CLEANUP_FILES", "true").lower() == "true":
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception:
                pass
