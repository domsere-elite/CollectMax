import os
import os
import hashlib
import uuid
import requests
import base64
from decimal import Decimal
from datetime import datetime
from typing import Optional, Dict, Any


class USAePayError(Exception):
    def __init__(self, message: str, data: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.data = data or {}


class USAePayDecline(USAePayError):
    pass

class USAePayService:
    def __init__(self):
        # Configuration
        self.api_key = os.getenv("USA_EPAY_API_KEY")
        self.api_pin = os.getenv("USA_EPAY_API_PIN")
        self.base_url = os.getenv("USA_EPAY_BASE_URL", "https://sandbox.usaepay.com/api/v2")

    def _generate_auth_header(self):
        """
        Generates the standard USA ePay authentication header.
        apiKey:s2/seed/sha256(apiKey + seed + apiPin)
        """
        if not self.api_key or not self.api_pin:
            raise ValueError("USA ePay credentials missing in environment.")

        seed = os.urandom(8).hex() # 16 chars
        pre_hash = f"{self.api_key}{seed}{self.api_pin}"
        auth_hash = hashlib.sha256(pre_hash.encode()).hexdigest()
        
        # apiHash = s2 + seed + hash
        api_hash = f"s2/{seed}/{auth_hash}"
        
        # authKey = base64(apiKey:apiHash)
        auth_str = f"{self.api_key}:{api_hash}"
        encoded_auth = base64.b64encode(auth_str.encode()).decode()
        
        return {
            "Authorization": f"Basic {encoded_auth}",
            "Content-Type": "application/json"
        }

    def tokenize_card(self, card_number: str, exp_date: str, cvv: str, holder_name: str, billing_address: Optional[Dict[str, Any]] = None):
        """
        Tokenizes a card using cc:save command on /transactions endpoint.
        Returns the card reference key (token).
        """
        url = f"{self.base_url}/transactions"
        
        creditcard = {
            "number": card_number,
            "expiration": exp_date,
            "cvc": cvv,
            "cardholder": holder_name
        }
        
        if billing_address:
            # USA ePay REST v2: specific AVS fields inside the creditcard object for cc:save
            if billing_address.get("address"): creditcard["avs_street"] = billing_address["address"]
            if billing_address.get("zip"): creditcard["avs_postalcode"] = str(billing_address["zip"])

        payload: Dict[str, Any] = {
            "command": "cc:save",
            "save_card": True,
            "creditcard": creditcard
        }
        
        response = requests.post(url, json=payload, headers=self._generate_auth_header())
        
        if response.status_code not in (200, 201):
           raise USAePayError(f"Tokenization failed: {response.status_code} - {response.text}")
        
        try:
            data = response.json()
        except ValueError:
            raise USAePayError(f"Tokenization response parse failed: {response.status_code} - {response.text}")
        if data.get("result_code") != "A":
            raise USAePayDecline(f"Tokenization Declined: {data.get('result')}", data)
            
        # The key is in savedcard.key
        return data.get("savedcard", {}).get("key")

    def run_transaction(self, token_id: str, amount: Decimal, invoice: str = "", customer_data: Optional[Dict[str, Any]] = None, stored_credential: Optional[str] = None):
        """
        Executes a sale charge against a saved token.
        """
        url = f"{self.base_url}/transactions"
        # Combine name for the 'cardholder' field which populates the 'Customer' column in the summary list
        full_name = ""
        if customer_data:
            full_name = f"{customer_data.get('first_name', '')} {customer_data.get('last_name', '')}".strip()

        payload: Dict[str, Any] = {
            "command": "sale",
            "save_card": False,
            "amount": str(amount),
            "invoice": str(invoice),
            "creditcard": {
                "number": token_id,
                "cardholder": full_name
            }
        }
        
        if customer_data:
            # USA ePay REST v2 requires lowercase keys for billing_address in transactions
            payload["billing_address"] = {
                "firstname": customer_data.get("first_name", ""),
                "lastname": customer_data.get("last_name", ""),
                "street": customer_data.get("address", ""),
                "street2": customer_data.get("address2", ""),
                "city": customer_data.get("city", ""),
                "state": customer_data.get("state", ""),
                "postalcode": str(customer_data.get("zip", "")),
                "country": "USA",
                "phone": customer_data.get("phone", "")
            }
            
            # Identification fields (Top Level)
            payload["customerid"] = customer_data.get("custid", "") # Often labeled "Consumer ID"
            payload["ponum"] = customer_data.get("custid", "") 
            payload["custid"] = customer_data.get("custid", "")
            payload["description"] = f"Payment for Portfolio Debt #{invoice}"
            payload["email"] = customer_data.get("email", "")

            # Nested customer object for name and secondary metadata
            payload["customer"] = {
                "first_name": customer_data.get("first_name", ""),
                "last_name": customer_data.get("last_name", ""),
                "email": customer_data.get("email", "")
            }

            # Optional: Traits for debt collection (if required by gateway)
            traits: Dict[str, Any] = {
                "is_debt": True
            }
            if stored_credential:
                traits["stored_credential"] = stored_credential
            payload["traits"] = traits
        
        response = requests.post(url, json=payload, headers=self._generate_auth_header())
        
        if response.status_code not in (200, 201):
            raise USAePayError(f"Transaction Request Failed: {response.status_code} - {response.text}")
            
        try:
            data = response.json()
        except ValueError:
            raise USAePayError(f"Transaction Response Parse Failed: {response.status_code} - {response.text}")
        if data.get("result_code") != "A":
            raise USAePayDecline(f"Transaction Declined: {data.get('result')}", data)
            
        return data

    @staticmethod
    def _extract_saved_card_key(data: dict):
        saved_card = data.get("savedcard") or {}
        return saved_card.get("key") or data.get("cardref")

    def run_payment_key_sale(self, payment_key: str, amount: Decimal, invoice: str = "", customer_data: Optional[Dict[str, Any]] = None, stored_credential: Optional[str] = None, save_card: bool = True):
        """
        Executes a sale using a Pay.js payment_key. Optionally saves the card for future use.
        Returns the response data and the saved card token (if save_card=True).
        """
        url = f"{self.base_url}/transactions"

        payload: Dict[str, Any] = {
            "command": "sale",
            "amount": str(amount),
            "invoice": str(invoice),
            "payment_key": payment_key,
            "save_card": bool(save_card)
        }

        if customer_data:
            payload["billing_address"] = {
                "firstname": customer_data.get("first_name", ""),
                "lastname": customer_data.get("last_name", ""),
                "street": customer_data.get("address", ""),
                "street2": customer_data.get("address2", ""),
                "city": customer_data.get("city", ""),
                "state": customer_data.get("state", ""),
                "postalcode": str(customer_data.get("zip", "")),
                "country": "USA",
                "phone": customer_data.get("phone", "")
            }
            payload["customerid"] = customer_data.get("custid", "")
            payload["ponum"] = customer_data.get("custid", "")
            payload["custid"] = customer_data.get("custid", "")
            payload["description"] = f"Payment for Portfolio Debt #{invoice}"
            payload["email"] = customer_data.get("email", "")
            payload["customer"] = {
                "first_name": customer_data.get("first_name", ""),
                "last_name": customer_data.get("last_name", ""),
                "email": customer_data.get("email", "")
            }
            traits: Dict[str, Any] = {
                "is_debt": True
            }
            if stored_credential:
                traits["stored_credential"] = stored_credential
            payload["traits"] = traits

        response = requests.post(url, json=payload, headers=self._generate_auth_header())

        if response.status_code not in (200, 201):
            raise USAePayError(f"Transaction Request Failed: {response.status_code} - {response.text}")

        try:
            data = response.json()
        except ValueError:
            raise USAePayError(f"Transaction Response Parse Failed: {response.status_code} - {response.text}")
        if data.get("result_code") != "A":
            raise USAePayDecline(f"Transaction Declined: {data.get('result')}", data)

        token = self._extract_saved_card_key(data) if save_card else None
        if save_card and not token:
            raise Exception("Transaction approved but no saved card token returned.")

        data["saved_card_key"] = token
        return data

    def run_payment_key_authonly(self, payment_key: str, amount: Decimal, invoice: str = "", customer_data: Optional[Dict[str, Any]] = None, stored_credential: Optional[str] = None):
        """
        Executes an auth-only transaction using a Pay.js payment_key.
        Returns the response data.
        """
        url = f"{self.base_url}/transactions"

        payload: Dict[str, Any] = {
            "command": "authonly",
            "amount": str(amount),
            "invoice": str(invoice),
            "payment_key": payment_key
        }

        if customer_data:
            payload["billing_address"] = {
                "firstname": customer_data.get("first_name", ""),
                "lastname": customer_data.get("last_name", ""),
                "street": customer_data.get("address", ""),
                "street2": customer_data.get("address2", ""),
                "city": customer_data.get("city", ""),
                "state": customer_data.get("state", ""),
                "postalcode": str(customer_data.get("zip", "")),
                "country": "USA",
                "phone": customer_data.get("phone", "")
            }
            payload["customerid"] = customer_data.get("custid", "")
            payload["ponum"] = customer_data.get("custid", "")
            payload["custid"] = customer_data.get("custid", "")
            payload["description"] = f"Payment for Portfolio Debt #{invoice}"
            payload["email"] = customer_data.get("email", "")
            payload["customer"] = {
                "first_name": customer_data.get("first_name", ""),
                "last_name": customer_data.get("last_name", ""),
                "email": customer_data.get("email", "")
            }
            traits: Dict[str, Any] = {
                "is_debt": True
            }
            if stored_credential:
                traits["stored_credential"] = stored_credential
            payload["traits"] = traits

        response = requests.post(url, json=payload, headers=self._generate_auth_header())

        if response.status_code not in (200, 201):
            raise USAePayError(f"Auth Request Failed: {response.status_code} - {response.text}")

        try:
            data = response.json()
        except ValueError:
            raise USAePayError(f"Auth Response Parse Failed: {response.status_code} - {response.text}")
        if data.get("result_code") != "A":
            raise USAePayDecline(f"Auth Declined: {data.get('result')}", data)

        return data

    def create_token_from_transaction(self, trankey: str) -> Dict[str, Any]:
        """
        Creates a reusable token from a prior transaction using its trankey.
        """
        url = f"{self.base_url}/tokens"
        payload: Dict[str, Any] = {
            "trankey": trankey
        }

        response = requests.post(url, json=payload, headers=self._generate_auth_header())

        if response.status_code not in (200, 201):
            raise USAePayError(f"Token creation failed: {response.status_code} - {response.text}")

        try:
            data = response.json()
        except ValueError:
            raise USAePayError(f"Token creation response parse failed: {response.status_code} - {response.text}")
        if not data.get("cardref"):
            raise USAePayError("Token creation failed: cardref not returned.")

        return data

    def void_transaction(self, ref_num: str):
        """
        Voids a previous transaction.
        """
        url = f"{self.base_url}/transactions/{ref_num}/void"
        response = requests.post(url, headers=self._generate_auth_header())
        
        if response.status_code != 200:
            raise USAePayError(f"Void Failed: {response.status_code} - {response.text}")

        if not response.text:
            return {"status": "voided", "refnum": ref_num}

        try:
            return response.json()
        except ValueError:
            return {"status": "voided", "refnum": ref_num, "raw": response.text}

    def verify_connection(self):
        """
        Verifies the connection to USA ePay by fetching basic account info.
        """
        url = f"{self.base_url}/account"
        try:
            response = requests.get(url, headers=self._generate_auth_header())
            if response.status_code == 200:
                # Success - authentication is valid
                return True, "Account Verified"
            else:
                return False, f"Connection Failed: {response.status_code} - {response.text}"
        except Exception as e:
            return False, f"Request Exception: {str(e)}"

    def fetch_account(self) -> Dict[str, Any]:
        """
        Fetches account information for debugging.
        """
        url = f"{self.base_url}/account"
        response = requests.get(url, headers=self._generate_auth_header())
        content_type = response.headers.get("Content-Type", "")
        data: Dict[str, Any] = {
            "status_code": response.status_code,
            "content_type": content_type,
            "text": response.text
        }
        try:
            data["json"] = response.json()
        except ValueError:
            data["json"] = None

        if response.status_code != 200:
            raise Exception(f"Account lookup failed: {response.status_code}")

        return data
