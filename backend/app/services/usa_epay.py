import os
import hashlib
import uuid
import requests
import base64
from decimal import Decimal
from datetime import datetime

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

    def tokenize_card(self, card_number: str, exp_date: str, cvv: str, holder_name: str, billing_address: dict = None):
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

        payload = {
            "command": "cc:save",
            "save_card": True,
            "creditcard": creditcard
        }
        
        print(f"DEBUG: USA ePay cc:save payload: {payload}")
        response = requests.post(url, json=payload, headers=self._generate_auth_header())
        print(f"DEBUG: USA ePay cc:save response: {response.status_code} - {response.text}")
        
        if response.status_code != 201 and response.status_code != 200:
           raise Exception(f"Tokenization failed: {response.text}")
        
        data = response.json()
        if data.get("result_code") != "A":
            raise Exception(f"Tokenization Declined: {data.get('result')}")
            
        # The key is in savedcard.key
        return data.get("savedcard", {}).get("key")

    def run_transaction(self, token_id: str, amount: Decimal, invoice: str = "", customer_data: dict = None):
        """
        Executes a sale charge against a saved token.
        """
        url = f"{self.base_url}/transactions"
        # Combine name for the 'cardholder' field which populates the 'Customer' column in the summary list
        full_name = ""
        if customer_data:
            full_name = f"{customer_data.get('first_name', '')} {customer_data.get('last_name', '')}".strip()

        payload = {
            "command": "sale",
            "save_card": True,
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
            payload["traits"] = {
                "is_debt": True
            }
        
        print(f"DEBUG: USA ePay sale payload: {payload}")
        response = requests.post(url, json=payload, headers=self._generate_auth_header())
        print(f"DEBUG: USA ePay sale response: {response.status_code} - {response.text}")
        
        if response.status_code != 201 and response.status_code != 200:
            raise Exception(f"Transaction Request Failed: {response.text}")
            
        data = response.json()
        if data.get("result_code") != "A":
            raise Exception(f"Transaction Declined: {data.get('result')}")
            
        return data

    def void_transaction(self, ref_num: str):
        """
        Voids a previous transaction.
        """
        url = f"{self.base_url}/transactions/{ref_num}/void"
        response = requests.post(url, headers=self._generate_auth_header())
        
        if response.status_code != 200:
            raise Exception(f"Void Failed: {response.text}")
            
        return response.json()

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
