"""
External Integrations Service
FastAPI service for third-party integrations and external data sources
"""

import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from .agentic_external_manager import AgenticExternalDataManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize external data manager
external_manager = AgenticExternalDataManager()

# FastAPI app
app = FastAPI(
    title="External Integrations Service",
    description="Third-party integrations and external data sources for insurance claims",
    version="1.0.0"
)

# Request/Response models
class ExternalDataRequest(BaseModel):
    source: str
    query_params: Dict[str, Any]
    claim_id: Optional[str] = None

class ExternalDataResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    processing_time_ms: int

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "external-integrations"}

@app.post("/query", response_model=ExternalDataResponse)
async def query_external_data(request: ExternalDataRequest):
    """Query external data sources"""
    try:
        result = await external_manager.query_external_data(
            source=request.source,
            query_params=request.query_params
        )

        return ExternalDataResponse(
            success=True,
            data=result.data,
            processing_time_ms=result.processing_time_ms
        )
    except Exception as e:
        logger.error(f"External data query failed: {str(e)}")
        return ExternalDataResponse(
            success=False,
            error=str(e),
            processing_time_ms=0
        )

@app.get("/sources")
async def get_available_sources():
    """Get list of available external data sources"""
    return {
        "sources": [
            "fraud_database",
            "vehicle_data",
            "weather_data",
            "geolocation",
            "identity_verification",
            "court_records",
            "property_data"
        ]
    }

@app.get("/stats")
async def get_processing_stats():
    """Get processing statistics"""
    return external_manager.processing_stats

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)