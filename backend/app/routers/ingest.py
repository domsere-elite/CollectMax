from fastapi import APIRouter, UploadFile, File, BackgroundTasks
from app.services.ingest import CSVImporter

router = APIRouter()

@router.post("/upload")
async def upload_portfolio(file: UploadFile = File(...), background_tasks: BackgroundTasks = None):
    """
    Accepts a CSV file upload and processes it in the background.
    """
    content = await file.read()
    text_content = content.decode('utf-8')
    
    # Initialize Importer
    importer = CSVImporter(text_content)
    
    # Process synchronously for now
    # Hardcoded portfolio_id=1 as seeded
    try:
        rows_processed = importer.process(portfolio_id=1)
        return {"status": "Success", "filename": file.filename, "rows_processed": rows_processed}
    except Exception as e:
        return {"status": "Error", "filename": file.filename, "error": str(e)}
