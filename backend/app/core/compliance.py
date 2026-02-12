from fastapi import APIRouter, HTTPException
from datetime import datetime, time
import pytz

router = APIRouter()

# Static Timezone Map (Stub for Example)
ZIP_TIMEZONE_MAP = {
    "90210": "America/Los_Angeles",
    "10001": "America/New_York",
    "60601": "America/Chicago"
}

class ComplianceError(Exception):
    pass

def check_calling_hours(zip_code: str):
    """
    Validates if the current time at the debtor's zip code is within 8AM - 9PM.
    Raises ComplianceError if outside allowed window.
    """
    tz_name = ZIP_TIMEZONE_MAP.get(zip_code)
    if not tz_name:
        # Default to UTC or fail safe? For compliance, strict adherence means we might block or default to strict.
        # Assuming safe default: Block if unknown, or default to checking server time if that was the rule (it's not).
        # We will allow it for now but flag it, or simplistic stub returns True.
        # Let's be strict:
        # Default to strict compliance: If ZIP is unknown, we cannot determine time, so we must BLOCK.
        # Unless override is enabled.
        import os
        if os.getenv("COMPLIANCE_ALLOW_UNKNOWN_ZIP", "false").lower() == "true":
            return True
        raise ComplianceError(f"Compliance Block: Unknown timezone for ZIP {zip_code}. Cannot verify calling hours.") 
        # Re-reading prompt: "Timezone Check: ... If outside 8AM-9PM local, raise ComplianceError."
        # If I don't know the TZ, I can't know the time. I'll default to failing safe (ComplianceError) or just passing for this stub.
        # I'll just pass for unknown zips to avoid breaking everything, but implement the logic for known ones.
        # pass 

    if tz_name:
        tz = pytz.timezone(tz_name)
        now = datetime.now(tz).time()
        start = time(8, 0)
        end = time(21, 0)
        
        if not (start <= now <= end):
            raise ComplianceError(f"Do Not Call: Current time {now} in {tz_name} is outside 8AM-9PM window.")
    
    return True

@router.get("/check-call-window/{zip_code}")
def api_check_call_window(zip_code: str):
    try:
        check_calling_hours(zip_code)
        return {"status": "ALLOWED"}
    except ComplianceError as e:
        raise HTTPException(status_code=403, detail=str(e))
