import psycopg2
from app.core.database import get_db_connection

def initialize_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 1. Existing Tables (Ensuring they exist)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS portfolios (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                commission_percentage DECIMAL(5,2) DEFAULT 30.00,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS debtors (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                ssn_hash VARCHAR(255) UNIQUE NOT NULL,
                first_name VARCHAR(255),
                last_name VARCHAR(255),
                dob DATE,
                address_1 VARCHAR(255),
                address_2 VARCHAR(255),
                city VARCHAR(255),
                state VARCHAR(50),
                zip_code VARCHAR(20),
                phone VARCHAR(20),
                mobile_consent BOOLEAN DEFAULT FALSE,
                email VARCHAR(255),
                do_not_contact BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        cursor.execute("SELECT 1 FROM pg_type WHERE typname = 'debt_status'")
        if not cursor.fetchone():
            cursor.execute("CREATE TYPE debt_status AS ENUM ('New', 'Plan', 'Paid', 'Closed', 'Disputed')")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS debts (
                id SERIAL PRIMARY KEY,
                debtor_id UUID REFERENCES debtors(id),
                portfolio_id INTEGER REFERENCES portfolios(id),
                client_reference_number VARCHAR(255),
                original_account_number VARCHAR(255) NOT NULL,
                original_creditor VARCHAR(255),
                current_creditor VARCHAR(255),
                date_opened DATE,
                charge_off_date DATE,
                principal_balance DECIMAL(15,2),
                fees_costs DECIMAL(15,2),
                face_value DECIMAL(15,2),
                amount_due DECIMAL(15,2),
                last_payment_date DATE,
                last_payment_amount DECIMAL(15,2),
                total_paid_amount DECIMAL(15,2) DEFAULT 0.00,
                last_payment_id INTEGER,
                last_payment_reference VARCHAR(255),
                last_payment_method VARCHAR(50),
                status debt_status DEFAULT 'New',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS interaction_logs (
                id SERIAL PRIMARY KEY,
                debt_id INTEGER REFERENCES debts(id),
                action_type VARCHAR(50),
                notes TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id SERIAL PRIMARY KEY,
                debt_id INTEGER REFERENCES debts(id),
                amount_paid DECIMAL(15,2) NOT NULL,
                agency_portion DECIMAL(15,2),
                client_portion DECIMAL(15,2),
                transaction_reference VARCHAR(255),
                scheduled_payment_id INTEGER,
                payment_method VARCHAR(50),
                status VARCHAR(20) DEFAULT 'paid',
                result_code VARCHAR(10),
                result VARCHAR(255),
                decline_reason VARCHAR(50),
                error_message TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # 2. NEW TABLES for Advanced Payment Module
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS payment_plans (
                id SERIAL PRIMARY KEY,
                debt_id INTEGER REFERENCES debts(id),
                total_settlement_amount DECIMAL(15,2) NOT NULL,
                down_payment_amount DECIMAL(15,2) DEFAULT 0.00,
                installment_count INTEGER NOT NULL,
                frequency VARCHAR(50) NOT NULL, -- 'weekly', 'bi-weekly', 'monthly'
                start_date DATE NOT NULL,
                card_token VARCHAR(255), -- USA ePay Card Reference Key
                status VARCHAR(50) DEFAULT 'active', -- 'active', 'completed', 'cancelled'
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scheduled_payments (
                id SERIAL PRIMARY KEY,
                plan_id INTEGER REFERENCES payment_plans(id) ON DELETE CASCADE,
                amount DECIMAL(15,2) NOT NULL,
                due_date DATE NOT NULL,
                status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'paid', 'missed', 'cancelled', 'declined', 'retrying', 'processing'
                actual_payment_id INTEGER REFERENCES payments(id),
                processed_at TIMESTAMP DEFAULT NULL,
                transaction_reference VARCHAR(255),
                payment_method VARCHAR(50),
                attempt_count INTEGER DEFAULT 0,
                next_attempt_at TIMESTAMP DEFAULT NULL,
                last_attempt_at TIMESTAMP DEFAULT NULL,
                last_gateway_trankey VARCHAR(255),
                last_result_code VARCHAR(10),
                last_result VARCHAR(255),
                last_decline_reason VARCHAR(50),
                last_error TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # 3. Seed initial data if portfolios is empty
        cursor.execute("SELECT COUNT(*) FROM portfolios")
        result = cursor.fetchone()
        if result and result[0] == 0:
            cursor.execute("INSERT INTO portfolios (name, commission_percentage) VALUES ('Standard Portfolio', 30.0)")
            print("Seeded initial portfolio.")

        conn.commit()
        print("Database initialized successfully.")
        
    except Exception as e:
        conn.rollback()
        print(f"Error initializing DB: {e}")
        raise e
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    initialize_db()
