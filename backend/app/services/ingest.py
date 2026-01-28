import csv
import io
import uuid
import hashlib
import re
from datetime import datetime
from decimal import Decimal

class CSVImporter:
    def __init__(self, file_content: str):
        self.file_content = file_content

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

    def hash_ssn(self, ssn: str):
        if not ssn:
            return "MISSING_SSN" # Or handle error
        return hashlib.sha256(ssn.encode()).hexdigest()

    def clean_decimal(self, value):
        if not value:
            return Decimal("0.00")
        return Decimal(value.replace('$', '').replace(',', ''))

    def process(self, portfolio_id: int):
        """
        Main entry point. Returns stats.
        """
        rows_processed = 0
        reader = csv.DictReader(io.StringIO(self.file_content))
        
        # Debugging: Write headers to a log file
        with open("ingest_debug.log", "w") as f:
            f.write(f"Detected Headers: {reader.fieldnames}\n")
            
        normalized_rows = []
        for row in reader:
            # Debugging: Log the first row raw
            if rows_processed == 0:
                with open("ingest_debug.log", "a") as f:
                    f.write(f"First Row Raw: {row}\n")
            
            clean_row = {self.normalize_header(k): v for k, v in row.items()}
            
            # Debugging: Log the first row cleaned
            if rows_processed == 0:
                 with open("ingest_debug.log", "a") as f:
                    f.write(f"First Row Cleaned: {clean_row}\n")

            self.process_row(clean_row, portfolio_id)
            rows_processed += 1
            
        return rows_processed

    def process_row(self, row, portfolio_id: int):
        # 1. Parsing & Sanitization
        ssn_hash = self.hash_ssn(row.get('ssn'))
        phone = self.sanitize_phone(row.get('primary_phone'))
        zip_5 = row.get('zip_code', '')[:5]
        
        dob = self.parse_date(row.get('date_of_birth'))
        
        # 2. Debtor Logic (Stub - Find or Create)
        debtor_data = {
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
            "mobile_consent": row.get('mobile_consent', 'False').lower() == 'true',
            "email": row.get('email_address')
        }
        
        debtor_id = self.find_or_create_debtor(debtor_data)
        
        # 3. Debt Logic
        debt_data = {
            "client_reference_number": row.get('client_reference'),
            "original_account_number": row.get('original_account'),
            "original_creditor": row.get('original_creditor'),
            "date_opened": self.parse_date(row.get('date_opened')),
            "charge_off_date": self.parse_date(row.get('charge_off_date')),
            "principal_balance": self.clean_decimal(row.get('principal_balance')),
            "fees_costs": self.clean_decimal(row.get('fees_costs')),
            "amount_due": self.clean_decimal(row.get('total_placed')),
            "last_payment_date": self.parse_date(row.get('last_payment_date')),
            "last_payment_amount": self.clean_decimal(row.get('last_payment_amt'))
        }
        
        self.create_debt(debtor_id, portfolio_id, debt_data)

    def create_debt(self, debtor_id, portfolio_id, data):
        conn = self.get_db()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO debts (
                    debtor_id, portfolio_id, client_reference_number, original_account_number,
                    original_creditor, date_opened, charge_off_date, principal_balance,
                    fees_costs, amount_due, last_payment_date, last_payment_amount, status
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'New'
                ) RETURNING id
            """, (
                str(debtor_id), portfolio_id, data['client_reference_number'], data['original_account_number'],
                data['original_creditor'], data['date_opened'], data['charge_off_date'], data['principal_balance'],
                data['fees_costs'], data['amount_due'], data['last_payment_date'], data['last_payment_amount']
            ))
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"Error creating debt: {e}")
            raise e
        finally:
            cursor.close()
            conn.close()

    def find_or_create_debtor(self, data):
        conn = self.get_db()
        cursor = conn.cursor()
        try:
            # Try to find existing debtor by ssn_hash
            cursor.execute("SELECT id FROM debtors WHERE ssn_hash = %s", (data['ssn_hash'],))
            result = cursor.fetchone()
            
            if result:
                return result[0]
            
            # Create new debtor
            cursor.execute("""
                INSERT INTO debtors (
                    ssn_hash, first_name, last_name, dob, address_1, address_2,
                    city, state, zip_code, phone, mobile_consent, email
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                ) RETURNING id
            """, (
                data['ssn_hash'], data['first_name'], data['last_name'], data['dob'],
                data['address_1'], data['address_2'], data['city'], data['state'],
                data['zip_code'], data['phone'], data['mobile_consent'], data['email']
            ))
            new_id = cursor.fetchone()[0]
            conn.commit()
            return new_id
        except Exception as e:
            conn.rollback()
            print(f"Error finding/creating debtor: {e}")
            raise e
        finally:
            cursor.close()
            conn.close()

    def get_db(self):
        from app.core.database import get_db_connection
        return get_db_connection()
