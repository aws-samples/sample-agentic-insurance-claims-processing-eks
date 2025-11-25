"""
Main FastAPI Application for Intelligent Loan Underwriting System
Provides 4 persona portals: Applicant, Loan Officer, Risk Manager, Executive
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import os
import sys

from fastapi import FastAPI, HTTPException, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel
import uvicorn
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import re

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database_models import (
    LoanApplication, LoanStatus, LoanType, RiskLevel,
    Address, Employment, FinancialInformation, LoanDetails,
    Document, UnderwritingMetrics
)
from agents.coordinator_agent import get_coordinator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# FastAPI Application Setup
# ============================================================================

app = FastAPI(
    title="Intelligent Loan Underwriting System",
    description="AI-Powered Multi-Agent Loan Processing on AWS EKS",
    version="1.0.0",
    docs_url=None if os.getenv("ENV") == "production" else "/docs",
    redoc_url=None if os.getenv("ENV") == "production" else "/redoc"
)

# Security Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    max_age=3600,
)

# Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    return response

# Templates
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

# MongoDB setup
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://mongodb-service:27017")
MONGODB_DB = os.getenv("MONGODB_DB", "loan_underwriting")

mongodb_client: Optional[AsyncIOMotorClient] = None
db = None

# Coordinator agent
coordinator = None


# ============================================================================
# Security Utilities
# ============================================================================

def sanitize_string(value: str, max_length: int = 255) -> str:
    """Sanitize string input to prevent injection attacks"""
    if not value:
        return ""
    # Remove any null bytes and limit length
    sanitized = value.replace('\x00', '').strip()[:max_length]
    return sanitized

def validate_application_id(application_id: str) -> bool:
    """Validate application ID format"""
    # Should match format: LOAN-YYYYMMDD-XXXXXXXX
    pattern = r'^LOAN-\d{8}-[a-f0-9]{8}$'
    return bool(re.match(pattern, application_id))

def sanitize_mongo_query(query: Dict) -> Dict:
    """Sanitize MongoDB queries to prevent NoSQL injection"""
    if not isinstance(query, dict):
        return {}

    sanitized = {}
    for key, value in query.items():
        # Remove keys starting with $ (MongoDB operators)
        if isinstance(key, str) and not key.startswith('$'):
            if isinstance(value, dict):
                sanitized[key] = sanitize_mongo_query(value)
            elif isinstance(value, str):
                sanitized[key] = sanitize_string(value)
            else:
                sanitized[key] = value
    return sanitized


# ============================================================================
# Custom Exception Handler
# ============================================================================

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Handle all exceptions and prevent information disclosure"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    # Don't expose internal error details in production
    if os.getenv("ENV") == "production":
        return JSONResponse(
            status_code=500,
            content={"detail": "An internal error occurred. Please try again later."}
        )
    else:
        return JSONResponse(
            status_code=500,
            content={"detail": f"Internal server error: {str(exc)}"}
        )


# ============================================================================
# Startup & Shutdown Events
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize connections on startup"""
    global mongodb_client, db, coordinator

    try:
        # Connect to MongoDB
        mongodb_client = AsyncIOMotorClient(MONGODB_URI)
        db = mongodb_client[MONGODB_DB]
        await db.command("ping")
        logger.info("Successfully connected to MongoDB")

        # Initialize coordinator
        coordinator = get_coordinator()
        logger.info("Loan underwriting coordinator initialized")

    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global mongodb_client

    if mongodb_client:
        mongodb_client.close()
        logger.info("MongoDB connection closed")


# ============================================================================
# Pydantic Models for API
# ============================================================================

class LoanApplicationRequest(BaseModel):
    """Request model for loan application submission"""
    # Borrower info
    borrower_first_name: str
    borrower_last_name: str
    borrower_email: str
    borrower_phone: str
    date_of_birth: str
    ssn_last_4: str

    # Address
    street: str
    city: str
    state: str
    zip_code: str
    residence_type: str = "own"
    years_at_address: float = 0

    # Employment
    employer_name: str
    employment_type: str
    job_title: str
    years_employed: float
    monthly_income: float

    # Financial
    annual_income: float
    other_income: float = 0
    monthly_debts: float = 0
    credit_score: Optional[int] = None

    # Loan details
    loan_type: str
    requested_amount: float
    loan_term_months: int
    loan_purpose: str
    down_payment: float = 0


class DecisionOverride(BaseModel):
    """Model for loan officer to override AI decision"""
    application_id: str
    override_decision: str  # approved, denied, conditionally_approved
    override_reason: str
    officer_name: str
    conditions: Optional[List[str]] = []


# ============================================================================
# HOME & HEALTH CHECK
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Landing page with portal selection"""
    return templates.TemplateResponse("index.html", {
        "request": request,
        "title": "Intelligent Loan Underwriting System"
    })


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check MongoDB
        await db.command("ping")
        mongo_status = "healthy"
    except:
        mongo_status = "unhealthy"

    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "mongodb": mongo_status,
        "coordinator": "healthy" if coordinator else "unhealthy"
    }


# ============================================================================
# APPLICANT PORTAL
# ============================================================================

@app.get("/applicant", response_class=HTMLResponse)
async def applicant_portal(request: Request):
    """Applicant portal - submit loan applications"""
    return templates.TemplateResponse("applicant_portal.html", {
        "request": request,
        "loan_types": [lt.value for lt in LoanType]
    })


@app.post("/api/applications/submit")
async def submit_application(application: LoanApplicationRequest):
    """Submit a new loan application"""
    try:
        # Convert request to LoanApplication model
        loan_app = LoanApplication(
            borrower_first_name=application.borrower_first_name,
            borrower_last_name=application.borrower_last_name,
            borrower_email=application.borrower_email,
            borrower_phone=application.borrower_phone,
            date_of_birth=datetime.fromisoformat(application.date_of_birth),
            ssn_last_4=application.ssn_last_4,
            current_address=Address(
                street=application.street,
                city=application.city,
                state=application.state,
                zip_code=application.zip_code,
                residence_type=application.residence_type,
                years_at_address=application.years_at_address
            ),
            employment=Employment(
                employer_name=application.employer_name,
                employment_type=application.employment_type,
                job_title=application.job_title,
                years_employed=application.years_employed,
                monthly_income=application.monthly_income
            ),
            financial_info=FinancialInformation(
                annual_income=application.annual_income,
                monthly_income=application.monthly_income,
                other_income=application.other_income,
                monthly_debts=application.monthly_debts,
                credit_score=application.credit_score
            ),
            loan_details=LoanDetails(
                loan_type=LoanType(application.loan_type),
                requested_amount=application.requested_amount,
                loan_term_months=application.loan_term_months,
                purpose=application.loan_purpose,
                down_payment=application.down_payment
            ),
            status=LoanStatus.SUBMITTED
        )

        # Save to database
        app_dict = loan_app.dict(by_alias=True, exclude={"id"})
        result = await db.applications.insert_one(app_dict)
        application_id = loan_app.application_id

        logger.info(f"Application {application_id} submitted successfully")

        # Trigger async underwriting process (don't wait for it)
        asyncio.create_task(process_application_async(application_id))

        return {
            "status": "success",
            "application_id": application_id,
            "message": "Application submitted successfully. Processing started."
        }

    except Exception as e:
        logger.error(f"Application submission failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to submit application")


@app.get("/api/applications/{application_id}")
async def get_application(application_id: str):
    """Get application details and status"""
    try:
        # Validate and sanitize input
        if not validate_application_id(application_id):
            raise HTTPException(status_code=400, detail="Invalid application ID format")

        sanitized_id = sanitize_string(application_id, max_length=50)

        app_data = await db.applications.find_one({"application_id": sanitized_id})

        if not app_data:
            raise HTTPException(status_code=404, detail="Application not found")

        # Convert ObjectId to string
        app_data['_id'] = str(app_data['_id'])

        return app_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve application: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve application")


async def process_application_async(application_id: str):
    """Process application asynchronously through AI workflow"""
    try:
        # Update status to underwriting
        await db.applications.update_one(
            {"application_id": application_id},
            {"$set": {
                "status": LoanStatus.UNDERWRITING.value,
                "last_updated": datetime.utcnow()
            }}
        )

        # Get application data
        app_data = await db.applications.find_one({"application_id": application_id})
        app_data['_id'] = str(app_data['_id'])

        # Process through coordinator
        logger.info(f"Processing {application_id} through AI workflow")
        result = await coordinator.process_application(app_data)

        # Determine final status
        decision = result.get('decision', {}).get('decision', 'denied')
        if decision == 'approved':
            final_status = LoanStatus.APPROVED
        elif decision == 'conditionally_approved':
            final_status = LoanStatus.CONDITIONALLY_APPROVED
        else:
            final_status = LoanStatus.DENIED

        # Update database with results
        await db.applications.update_one(
            {"application_id": application_id},
            {"$set": {
                "status": final_status.value,
                "credit_analysis": result.get('credit_analysis'),
                "income_verification": result.get('income_verification'),
                "risk_assessment": result.get('risk_assessment'),
                "compliance_check": result.get('compliance_check'),
                "underwriting_decision": result.get('decision'),
                "agent_activity": result.get('agent_logs', []),
                "processing_time_minutes": result.get('processing_time_seconds', 0) / 60,
                "last_updated": datetime.utcnow()
            }}
        )

        logger.info(f"Application {application_id} processed: {decision}")

    except Exception as e:
        logger.error(f"Application processing failed for {application_id}: {e}")
        await db.applications.update_one(
            {"application_id": application_id},
            {"$set": {
                "status": LoanStatus.DENIED.value,
                "underwriting_decision": {
                    "decision": "denied",
                    "denial_reasons": [f"Processing error: {str(e)}"],
                    "human_review_required": True
                },
                "last_updated": datetime.utcnow()
            }}
        )


# ============================================================================
# LOAN OFFICER PORTAL
# ============================================================================

@app.get("/officer", response_class=HTMLResponse)
async def officer_portal(request: Request):
    """Loan officer portal - review and manage applications"""
    return templates.TemplateResponse("officer_portal.html", {
        "request": request
    })


@app.get("/api/officer/pending")
async def get_pending_applications():
    """Get applications pending review"""
    try:
        # Get applications that need review
        cursor = db.applications.find({
            "$or": [
                {"status": LoanStatus.UNDERWRITING.value},
                {"underwriting_decision.human_review_required": True}
            ]
        }).sort("submitted_at", -1).limit(50)

        applications = []
        async for app in cursor:
            app['_id'] = str(app['_id'])
            applications.append(app)

        return {"applications": applications, "count": len(applications)}

    except Exception as e:
        logger.error(f"Failed to get pending applications: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve pending applications")


@app.post("/api/officer/override")
async def override_decision(override: DecisionOverride):
    """Loan officer overrides AI decision"""
    try:
        update_data = {
            "underwriting_decision.decision": override.override_decision,
            "underwriting_decision.human_reviewer": override.officer_name,
            "underwriting_decision.human_review_notes": override.override_reason,
            "underwriting_decision.human_review_required": False,
            "last_updated": datetime.utcnow()
        }

        if override.conditions:
            update_data["underwriting_decision.conditions"] = override.conditions

        # Update status based on decision
        if override.override_decision == "approved":
            update_data["status"] = LoanStatus.APPROVED.value
        elif override.override_decision == "conditionally_approved":
            update_data["status"] = LoanStatus.CONDITIONALLY_APPROVED.value
        else:
            update_data["status"] = LoanStatus.DENIED.value

        result = await db.applications.update_one(
            {"application_id": override.application_id},
            {"$set": update_data}
        )

        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Application not found")

        logger.info(f"Decision overridden for {override.application_id} by {override.officer_name}")

        return {"status": "success", "message": "Decision updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to override decision: {e}")
        raise HTTPException(status_code=500, detail="Failed to override decision")


# ============================================================================
# RISK MANAGER PORTAL
# ============================================================================

@app.get("/risk", response_class=HTMLResponse)
async def risk_portal(request: Request):
    """Risk manager portal - portfolio risk monitoring"""
    return templates.TemplateResponse("risk_portal.html", {
        "request": request
    })


@app.get("/api/risk/metrics")
async def get_risk_metrics():
    """Get portfolio risk metrics"""
    try:
        # Aggregate risk metrics
        pipeline = [
            {
                "$match": {
                    "status": {"$in": [
                        LoanStatus.APPROVED.value,
                        LoanStatus.CONDITIONALLY_APPROVED.value
                    ]}
                }
            },
            {
                "$group": {
                    "_id": "$risk_assessment.overall_risk_level",
                    "count": {"$sum": 1},
                    "total_amount": {"$sum": "$loan_details.requested_amount"},
                    "avg_probability_of_default": {"$avg": "$risk_assessment.probability_of_default"}
                }
            }
        ]

        risk_distribution = []
        async for doc in db.applications.aggregate(pipeline):
            risk_distribution.append(doc)

        # Get overall metrics
        total_apps = await db.applications.count_documents({})
        approved_apps = await db.applications.count_documents({
            "status": {"$in": [LoanStatus.APPROVED.value, LoanStatus.CONDITIONALLY_APPROVED.value]}
        })

        return {
            "risk_distribution": risk_distribution,
            "total_applications": total_apps,
            "approved_applications": approved_apps,
            "approval_rate": (approved_apps / total_apps * 100) if total_apps > 0 else 0
        }

    except Exception as e:
        logger.error(f"Failed to get risk metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve risk metrics")


# ============================================================================
# EXECUTIVE PORTAL
# ============================================================================

@app.get("/executive", response_class=HTMLResponse)
async def executive_portal(request: Request):
    """Executive portal - business intelligence dashboard"""
    return templates.TemplateResponse("executive_portal.html", {
        "request": request
    })


@app.get("/api/executive/kpis")
async def get_executive_kpis():
    """Get executive KPIs and metrics"""
    try:
        # Calculate KPIs
        total_apps = await db.applications.count_documents({})
        approved = await db.applications.count_documents({
            "status": {"$in": [LoanStatus.APPROVED.value, LoanStatus.CONDITIONALLY_APPROVED.value]}
        })
        denied = await db.applications.count_documents({"status": LoanStatus.DENIED.value})

        # Financial metrics
        pipeline = [
            {
                "$match": {
                    "status": {"$in": [LoanStatus.APPROVED.value, LoanStatus.CONDITIONALLY_APPROVED.value]}
                }
            },
            {
                "$group": {
                    "_id": None,
                    "total_loan_amount": {"$sum": "$underwriting_decision.approved_amount"},
                    "avg_loan_amount": {"$avg": "$underwriting_decision.approved_amount"},
                    "avg_interest_rate": {"$avg": "$underwriting_decision.interest_rate"},
                    "avg_processing_time": {"$avg": "$processing_time_minutes"}
                }
            }
        ]

        financial_metrics = None
        async for doc in db.applications.aggregate(pipeline):
            financial_metrics = doc

        # AI performance
        ai_decisions = await db.applications.count_documents({
            "underwriting_decision.human_review_required": False
        })
        human_overrides = await db.applications.count_documents({
            "underwriting_decision.human_reviewer": {"$exists": True}
        })

        return {
            "total_applications": total_apps,
            "approved_applications": approved,
            "denied_applications": denied,
            "approval_rate": (approved / total_apps * 100) if total_apps > 0 else 0,
            "total_loan_amount": financial_metrics.get('total_loan_amount', 0) if financial_metrics else 0,
            "avg_loan_amount": financial_metrics.get('avg_loan_amount', 0) if financial_metrics else 0,
            "avg_interest_rate": financial_metrics.get('avg_interest_rate', 0) if financial_metrics else 0,
            "avg_processing_time_minutes": financial_metrics.get('avg_processing_time', 0) if financial_metrics else 0,
            "ai_decisions": ai_decisions,
            "human_overrides": human_overrides,
            "ai_accuracy": ((ai_decisions - human_overrides) / ai_decisions * 100) if ai_decisions > 0 else 0
        }

    except Exception as e:
        logger.error(f"Failed to get executive KPIs: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve executive KPIs")


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )
