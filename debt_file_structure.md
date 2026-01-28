# Standard Debt File Data Points & Schema Mapping

## Overview
This document defines the standard data points expected in a client CSV upload for the "CollectSecure" platform. It maps raw CSV headers to the internal database schema, ensuring FDCPA compliance and accurate financial tracking.

---

## 1. Debtor Identity (The "Human")
*These fields belong in the `debtors` table. They are unique to the person.*

| Data Point | Data Type | Description | Compliance Note |
| :--- | :--- | :--- | :--- |
| **SSN** | String (Hash) | Social Security Number. **CRITICAL:** Store only as `SHA-256` hash. Never raw. | Used for Deduplication. |
| **First Name** | String | Debtor's first name. | |
| **Last Name** | String | Debtor's last name. | |
| **Date of Birth** | Date | Debtor's DOB. | Used for identity verification (Right Party Contact). |
| **Address Line 1** | String | Street address. | |
| **Address Line 2** | String | Apt, Suite, Unit. | |
| **City** | String | City. | |
| **State** | String (2) | 2-letter state code. | **CRITICAL:** Used for State Licensing checks. |
| **Zip Code** | String (5/9) | Postal code. | **CRITICAL:** Used for Timezone calculation (8am-9pm rule). |
| **Primary Phone** | String | Main contact number. | Clean non-numeric chars before storing. |
| **Mobile Consent** | Boolean | Did debtor consent to SMS? | Required for "Solutions By Text" integration. |
| **Email Address** | String | Primary email. | |

---

## 2. Account Details (The "File")
*These fields belong in the `debts` table. One Debtor can have multiple Debts.*

| Data Point | Data Type | Description | Compliance Note |
| :--- | :--- | :--- | :--- |
| **Client Reference #** | String | The unique ID assigned by the Client. | |
| **Original Account #** | String | The account number from the Original Creditor. | Required for validation notices. |
| **Original Creditor** | String | Name of the bank/lender who originated the debt. | Required for FDCPA "Mini-Miranda". |
| **Date Opened** | Date | Date the account was originally opened. | |
| **Charge-off Date** | Date | Date the debt was written off by creditor. | **CRITICAL:** Primary anchor for debt age since Delinquency Date is absent. |

---

## 3. Financials (The "Ledger")
*These fields determine the money owed. Stored in `debts` or derived tables.*

| Data Point | Data Type | Description | Compliance Note |
| :--- | :--- | :--- | :--- |
| **Principal Balance** | Decimal | The core amount owed. | |
| **Fees/Costs** | Decimal | Pre-placement collection costs. | |
| **Total Placed** | Decimal | The sum total due at time of import. | The "Amount Due" in the UI. |
| **Last Payment Date** | Date | Date of the last payment made to creditor. | Important for validating if debt is time-barred. |
| **Last Payment Amt** | Decimal | Amount of that last payment. | |

---

## 4. Portfolio Metadata (The "Business")
*These fields link the file to your agency's commission structure.*

| Data Point | Data Type | Description | Usage |
| :--- | :--- | :--- | :--- |
| **Client ID** | Integer | Internal ID for the creditor client. | Links to `clients` table. |
| **Portfolio Group** | String | Name of the specific portfolio batch (e.g., "Jan 2026 Placements"). | Links to `portfolios` table. |
| **Commission Rate** | Decimal | The fee % for this specific file (e.g., 0.30). | Used for Split Ledger calculations. |

---

## 5. CSV Ingest Mapping Rules (For The AI)
*When building the `CSVImporter` class, use this logic:*

1.  **Header Normalization:** Convert all incoming CSV headers to snake_case (e.g., "First Name" -> `first_name`).
2.  **Date Parsing:** Attempt multiple formats (MM/DD/YYYY, YYYY-MM-DD). If invalid, log error row.
3.  **Sanitization:**
    * `phone`: Strip `(` `)` `-` and spaces.
    * `ssn`: Hash immediately. Drop raw value.
    * `zip_code`: Take first 5 digits for timezone lookup.
4.  **Dedupe Check:**
    * `IF` ssn_hash exists in `debtors` `THEN` use existing `debtor_id`.
    * `ELSE` create new `debtor`.