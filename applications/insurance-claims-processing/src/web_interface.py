"""
Simple Web Interface for Claims Submission
Basic HTML form for testing the claims processing system with Human-in-the-Loop
"""

import uuid
import json
import aiohttp
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import os

from .database_models import db_manager

# Create web interface app
web_app = FastAPI(title="Insurance Claims Portal")

# Templates directory
templates_dir = os.path.join(os.path.dirname(__file__), "templates")
os.makedirs(templates_dir, exist_ok=True)

templates = Jinja2Templates(directory=templates_dir)

# Static files directory
static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)

web_app.mount("/static", StaticFiles(directory=static_dir), name="static")

@web_app.on_event("startup")
async def startup_event():
    """Initialize database connection"""
    await db_manager.connect()

@web_app.on_event("shutdown")
async def shutdown_event():
    """Close database connection"""
    await db_manager.disconnect()

@web_app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page with claim submission form"""
    return templates.TemplateResponse("claim_form.html", {"request": request})

@web_app.get("/claims", response_class=HTMLResponse)
async def list_claims(request: Request, page: int = 1):
    """List all claims with pagination (for demo purposes, limit to 100 most recent)"""
    page_size = 50
    skip = (page - 1) * page_size

    # For demo: only show most recent 100 claims
    claims = await db_manager.list_claims(skip=skip, limit=min(page_size, 100 - skip))

    # Get total count for pagination (capped at 100 for demo)
    total_claims = min(await db_manager.count_claims(), 100)
    total_pages = (total_claims + page_size - 1) // page_size

    return templates.TemplateResponse("claims_list.html", {
        "request": request,
        "claims": claims,
        "page": page,
        "total_pages": total_pages,
        "total_claims": total_claims
    })

@web_app.get("/claims/{claim_id}", response_class=HTMLResponse)
async def view_claim(request: Request, claim_id: str):
    """View specific claim details"""
    claim = await db_manager.get_claim(claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    return templates.TemplateResponse("claim_detail.html", {
        "request": request,
        "claim": claim
    })

@web_app.post("/submit-claim")
async def submit_claim(
    customer_name: str = Form(...),
    customer_email: str = Form(...),
    policy_number: str = Form(...),
    claim_type: str = Form(...),
    incident_date: str = Form(...),
    claim_amount: float = Form(...),
    description: str = Form(...)
):
    """Handle claim submission"""

    # Generate unique claim ID
    claim_id = f"CLM-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"

    # Prepare claim data
    claim_data = {
        "claim_id": claim_id,
        "customer_name": customer_name,
        "customer_email": customer_email,
        "policy_number": policy_number,
        "claim_type": claim_type,
        "incident_date": datetime.fromisoformat(incident_date),
        "claim_amount": claim_amount,
        "description": description,
        "status": "submitted",
        "current_stage": "initial_review"
    }

    # Save to database
    await db_manager.create_claim(claim_data)

    # Redirect to claim detail page
    return RedirectResponse(url=f"/claims/{claim_id}", status_code=303)

@web_app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "web_interface"}

@web_app.get("/human-review", response_class=HTMLResponse)
async def human_review_dashboard(request: Request, role: str = "claims_adjuster"):
    """Human review dashboard - shows pending tasks"""
    # Get pending tasks from coordinator
    try:
        async with aiohttp.ClientSession() as session:
            # Get pending tasks from human workflow manager (embedded in coordinator)
            async with session.get(
                f"http://coordinator-service:8000/human-tasks/{role}"
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    tasks = data.get("tasks", [])
                else:
                    tasks = []
    except Exception as e:
        tasks = []

    return templates.TemplateResponse("human_review.html", {
        "request": request,
        "tasks": tasks,
        "role": role
    })

@web_app.post("/submit-human-decision/{task_id}")
async def submit_human_decision(
    task_id: str,
    decision: str = Form(...),
    reasoning: str = Form(...),
    reviewer_id: str = Form(...),
    settlement_amount: Optional[float] = Form(None)
):
    """Submit human decision for a task"""

    decision_data = {
        "decision": decision,
        "reasoning": reasoning,
        "settlement_amount": settlement_amount
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"http://coordinator-service:8000/human-decision/{task_id}",
                json={
                    "decision": decision_data,
                    "reviewer_id": reviewer_id,
                    "reviewer_license": None
                }
            ) as response:
                result = await response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Redirect back to human review dashboard
    return RedirectResponse(url="/human-review", status_code=303)

# HTML Templates as strings (simple approach)
claim_form_html = """
<!DOCTYPE html>
<html>
<head>
    <title>Submit Insurance Claim</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; font-weight: bold; }
        input, select, textarea { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
        textarea { height: 100px; }
        button { background-color: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
        button:hover { background-color: #0056b3; }
        .header { text-align: center; margin-bottom: 30px; }
        .nav { margin-bottom: 20px; }
        .nav a { margin-right: 15px; text-decoration: none; color: #007bff; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🏥 Insurance Claims Portal</h1>
        <p>Human-in-the-Loop Claims Processing with AI Assistance</p>
    </div>

    <div class="nav">
        <a href="/">Submit Claim</a>
        <a href="/claims">View Claims</a>
        <a href="/human-review">👨‍💼 Human Review Queue</a>
    </div>

    <h2>Submit New Claim</h2>
    <form action="/submit-claim" method="post">
        <div class="form-group">
            <label for="customer_name">Customer Name:</label>
            <input type="text" id="customer_name" name="customer_name" required>
        </div>

        <div class="form-group">
            <label for="customer_email">Email:</label>
            <input type="email" id="customer_email" name="customer_email" required>
        </div>

        <div class="form-group">
            <label for="policy_number">Policy Number:</label>
            <input type="text" id="policy_number" name="policy_number" required>
        </div>

        <div class="form-group">
            <label for="claim_type">Claim Type:</label>
            <select id="claim_type" name="claim_type" required>
                <option value="">Select claim type</option>
                <option value="collision">Collision</option>
                <option value="comprehensive">Comprehensive</option>
                <option value="liability">Liability</option>
                <option value="property">Property Damage</option>
                <option value="theft">Theft</option>
                <option value="vandalism">Vandalism</option>
            </select>
        </div>

        <div class="form-group">
            <label for="incident_date">Incident Date:</label>
            <input type="date" id="incident_date" name="incident_date" required>
        </div>

        <div class="form-group">
            <label for="claim_amount">Claim Amount ($):</label>
            <input type="number" id="claim_amount" name="claim_amount" step="0.01" min="0" required>
        </div>

        <div class="form-group">
            <label for="description">Description of Incident:</label>
            <textarea id="description" name="description" placeholder="Please provide details about what happened..." required></textarea>
        </div>

        <button type="submit">Submit Claim</button>
    </form>
</body>
</html>
"""

claims_list_html = """
<!DOCTYPE html>
<html>
<head>
    <title>Claims List - Insurance Portal</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { text-align: center; margin-bottom: 30px; }
        .nav { margin-bottom: 20px; }
        .nav a { margin-right: 15px; text-decoration: none; color: #007bff; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #f8f9fa; }
        tr:hover { background-color: #f5f5f5; }
        .status { padding: 4px 8px; border-radius: 4px; font-size: 12px; }
        .status-submitted { background-color: #d4edda; color: #155724; }
        .status-processing { background-color: #d1ecf1; color: #0c5460; }
        .status-completed { background-color: #d1ecf1; color: #0c5460; }
        .amount { font-weight: bold; color: #28a745; }
        a { color: #007bff; text-decoration: none; }
        a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🏥 Insurance Claims Portal</h1>
        <p>Human-in-the-Loop Claims Processing with AI Assistance</p>
    </div>

    <div class="nav">
        <a href="/">Submit Claim</a>
        <a href="/claims">View Claims</a>
        <a href="/human-review">👨‍💼 Human Review Queue</a>
    </div>

    <h2>All Claims <small style="color: #6c757d; font-size: 0.6em;">(Showing most recent {{ total_claims }} for demo)</small></h2>

    {% if claims %}
    <table>
        <thead>
            <tr>
                <th>Claim ID</th>
                <th>Customer</th>
                <th>Type</th>
                <th>Amount</th>
                <th>Status</th>
                <th>Submitted</th>
                <th>Actions</th>
            </tr>
        </thead>
        <tbody>
            {% for claim in claims %}
            <tr>
                <td><code>{{ claim.claim_id }}</code></td>
                <td>{{ claim.customer_name }}</td>
                <td>{{ claim.claim_type.title() }}</td>
                <td class="amount">${{ "%.2f"|format(claim.claim_amount) }}</td>
                <td><span class="status status-{{ claim.status }}">{{ claim.status.title() }}</span></td>
                <td>{{ claim.created_at.strftime('%Y-%m-%d %H:%M') if claim.created_at else 'N/A' }}</td>
                <td><a href="/claims/{{ claim.claim_id }}">View Details</a></td>
            </tr>
            {% endfor %}
        </tbody>
    </table>

    {% if total_pages > 1 %}
    <div style="text-align: center; margin-top: 30px; padding: 20px;">
        {% if page > 1 %}
            <a href="/claims?page={{ page - 1 }}" style="padding: 8px 16px; margin: 0 5px; background-color: #007bff; color: white; text-decoration: none; border-radius: 4px;">« Previous</a>
        {% endif %}

        <span style="margin: 0 15px; color: #6c757d;">Page {{ page }} of {{ total_pages }}</span>

        {% if page < total_pages %}
            <a href="/claims?page={{ page + 1 }}" style="padding: 8px 16px; margin: 0 5px; background-color: #007bff; color: white; text-decoration: none; border-radius: 4px;">Next »</a>
        {% endif %}
    </div>
    {% endif %}
    {% else %}
    <p>No claims found. <a href="/">Submit your first claim</a>.</p>
    {% endif %}
</body>
</html>
"""

claim_detail_html = """
<!DOCTYPE html>
<html>
<head>
    <title>Claim {{ claim.claim_id }} - Insurance Portal</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        .header { text-align: center; margin-bottom: 30px; }
        .nav { margin-bottom: 20px; }
        .nav a { margin-right: 15px; text-decoration: none; color: #007bff; }
        .claim-header { background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .section { margin-bottom: 25px; padding: 15px; border: 1px solid #ddd; border-radius: 8px; }
        .section h3 { margin-top: 0; color: #495057; }
        .field { margin-bottom: 10px; }
        .field label { font-weight: bold; color: #6c757d; }
        .field value { margin-left: 10px; }
        .status { padding: 6px 12px; border-radius: 4px; font-weight: bold; }
        .status-submitted { background-color: #d4edda; color: #155724; }
        .amount { font-size: 1.2em; font-weight: bold; color: #28a745; }
        .description { background-color: #f8f9fa; padding: 15px; border-radius: 4px; line-height: 1.6; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🏥 Insurance Claims Portal</h1>
        <p>Human-in-the-Loop Claims Processing with AI Assistance</p>
    </div>

    <div class="nav">
        <a href="/">Submit Claim</a>
        <a href="/claims">View Claims</a>
        <a href="/human-review">👨‍💼 Human Review Queue</a>
    </div>

    <div class="claim-header">
        <h2>Claim {{ claim.claim_id }}</h2>
        <p><span class="status status-{{ claim.status }}">{{ claim.status.title() }}</span></p>
    </div>

    <div class="section">
        <h3>👤 Customer Information</h3>
        <div class="field">
            <label>Name:</label>
            <span class="value">{{ claim.customer_name }}</span>
        </div>
        <div class="field">
            <label>Email:</label>
            <span class="value">{{ claim.customer_email }}</span>
        </div>
        <div class="field">
            <label>Policy Number:</label>
            <span class="value">{{ claim.policy_number }}</span>
        </div>
    </div>

    <div class="section">
        <h3>📋 Claim Details</h3>
        <div class="field">
            <label>Type:</label>
            <span class="value">{{ claim.claim_type.title() }}</span>
        </div>
        <div class="field">
            <label>Incident Date:</label>
            <span class="value">{{ claim.incident_date.strftime('%Y-%m-%d') if claim.incident_date else 'N/A' }}</span>
        </div>
        <div class="field">
            <label>Reported Date:</label>
            <span class="value">{{ claim.reported_date.strftime('%Y-%m-%d %H:%M') if claim.reported_date else 'N/A' }}</span>
        </div>
        <div class="field">
            <label>Claim Amount:</label>
            <span class="value amount">${{ "%.2f"|format(claim.claim_amount) }}</span>
        </div>
    </div>

    <div class="section">
        <h3>📝 Description</h3>
        <div class="description">{{ claim.description }}</div>
    </div>

    {% if claim.ai_recommendation %}
    <div class="section">
        <h3>🤖 AI Analysis</h3>
        <pre>{{ claim.ai_recommendation | tojson(indent=2) }}</pre>
    </div>
    {% endif %}

    {% if claim.external_data_analysis %}
    <div class="section">
        <h3>🌐 External Data Intelligence (Agentic AI)</h3>
        {% set external_data = claim.external_data_analysis %}
        {% if external_data.processing_metadata %}
        <div class="field">
            <label>Data Sources Consulted:</label>
            <span class="value">{{ external_data.processing_metadata.sources_queried }}</span>
        </div>
        <div class="field">
            <label>Processing Cost:</label>
            <span class="value">{{ external_data.processing_metadata.cost }}</span>
        </div>
        <div class="field">
            <label>Processing Time:</label>
            <span class="value">{{ external_data.processing_metadata.processing_time_ms }}ms</span>
        </div>
        <div class="field">
            <label>Agentic Efficiency:</label>
            <span class="value">{{ external_data.processing_metadata.agentic_efficiency }}</span>
        </div>
        {% endif %}

        {% if external_data.agentic_analysis %}
        {% set analysis = external_data.agentic_analysis %}
        <h4>🚨 Risk Assessment</h4>
        <div class="field">
            <label>Composite Risk Score:</label>
            <span class="value">{{ "%.2f"|format(analysis.agentic_risk_assessment.composite_risk_score) }}</span>
        </div>
        <div class="field">
            <label>Risk Level:</label>
            <span class="value">{{ analysis.agentic_risk_assessment.risk_level }}</span>
        </div>
        <div class="field">
            <label>Total Risk Indicators:</label>
            <span class="value">{{ analysis.agentic_risk_assessment.total_risk_indicators }}</span>
        </div>

        <h4>🎯 Agentic Recommendations</h4>
        <div class="field">
            <label>Primary Recommendation:</label>
            <span class="value">{{ analysis.agentic_recommendations.primary_recommendation }}</span>
        </div>
        <div class="field">
            <label>Routing Decision:</label>
            <span class="value">{{ analysis.agentic_recommendations.routing_decision }}</span>
        </div>
        <div class="field">
            <label>Estimated Processing:</label>
            <span class="value">{{ analysis.agentic_recommendations.estimated_processing_time }}</span>
        </div>

        {% if analysis.all_risk_indicators %}
        <h4>🔍 Risk Indicators</h4>
        <ul>
        {% for indicator in analysis.all_risk_indicators %}
            <li>{{ indicator }}</li>
        {% endfor %}
        </ul>
        {% endif %}

        {% if analysis.all_agentic_insights %}
        <h4>💡 Agentic Insights</h4>
        <ul>
        {% for insight in analysis.all_agentic_insights %}
            <li>{{ insight }}</li>
        {% endfor %}
        </ul>
        {% endif %}
        {% endif %}

        <details style="margin-top: 15px;">
            <summary>📊 Raw External Data (Click to expand)</summary>
            <pre style="background-color: #f8f9fa; padding: 10px; border-radius: 4px; font-size: 12px; max-height: 400px; overflow-y: auto;">{{ claim.external_data_analysis | tojson(indent=2) }}</pre>
        </details>
    </div>
    {% endif %}

    {% if claim.human_decision %}
    <div class="section" style="background-color: #d4edda; border-left: 4px solid #28a745;">
        <h3>👨‍💼 Human Decision Recorded</h3>
        <div class="field">
            <label>Decision:</label>
            <span class="value" style="font-weight: bold; font-size: 1.1em;">{{ claim.human_decision.get('decision', 'N/A').upper() }}</span>
        </div>
        <div class="field">
            <label>Reviewed By:</label>
            <span class="value">{{ claim.get('reviewed_by', 'N/A') }}</span>
        </div>
        <div class="field">
            <label>Review Date:</label>
            <span class="value">{{ claim.reviewed_at.strftime('%Y-%m-%d %H:%M') if claim.get('reviewed_at') else 'N/A' }}</span>
        </div>
        {% if claim.human_decision.get('settlement_amount') %}
        <div class="field">
            <label>Settlement Amount:</label>
            <span class="value amount">${{ "%.2f"|format(claim.human_decision.get('settlement_amount', 0)) }}</span>
        </div>
        {% endif %}
        <div class="field">
            <label>Reasoning:</label>
            <div style="background-color: white; padding: 10px; border-radius: 4px; margin-top: 5px; line-height: 1.6;">
                {{ claim.human_decision.get('reasoning', 'No reasoning provided') }}
            </div>
        </div>
    </div>
    {% endif %}

    <div class="section">
        <h3>📜 Audit Trail</h3>
        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 4px;">
            <div class="field">
                <label>Created:</label>
                <span class="value">{{ claim.created_at.strftime('%Y-%m-%d %H:%M:%S') if claim.created_at else 'N/A' }}</span>
            </div>
            <div class="field">
                <label>Last Updated:</label>
                <span class="value">{{ claim.updated_at.strftime('%Y-%m-%d %H:%M:%S') if claim.updated_at else 'N/A' }}</span>
            </div>
            <div class="field">
                <label>Current Stage:</label>
                <span class="value">{{ claim.current_stage.replace('_', ' ').title() }}</span>
            </div>
            {% if claim.assigned_adjuster %}
            <div class="field">
                <label>Assigned To:</label>
                <span class="value">{{ claim.assigned_adjuster }}</span>
            </div>
            {% endif %}
        </div>

        <div style="margin-top: 15px; padding: 10px; background-color: #fff3cd; border-left: 4px solid #ffc107; border-radius: 4px;">
            <strong>🔒 Compliance Note:</strong> All claim processing activities are logged and auditable per regulatory requirements.
            Human decisions are permanently recorded with reviewer identification and timestamp.
        </div>
    </div>
</body>
</html>
"""

human_review_html = """
<!DOCTYPE html>
<html>
<head>
    <title>Human Review Dashboard - Insurance Portal</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; max-width: 1400px; margin: 0 auto; padding: 20px; background-color: #f5f5f5; }
        .header { text-align: center; margin-bottom: 30px; background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .nav { margin-bottom: 20px; background-color: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .nav a { margin-right: 20px; text-decoration: none; color: #007bff; font-weight: 500; }
        .nav a:hover { text-decoration: underline; }
        .role-selector { margin-bottom: 20px; background-color: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .role-selector select { padding: 8px; font-size: 14px; border: 1px solid #ddd; border-radius: 4px; }
        .task-card { background-color: white; padding: 20px; margin-bottom: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); border-left: 4px solid #007bff; }
        .task-card.high-priority { border-left-color: #dc3545; }
        .task-card.urgent { border-left-color: #ffc107; background-color: #fffbea; }
        .task-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; border-bottom: 2px solid #f0f0f0; padding-bottom: 10px; }
        .task-id { font-weight: bold; color: #495057; font-size: 14px; }
        .priority-badge { padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: bold; text-transform: uppercase; }
        .priority-high { background-color: #dc3545; color: white; }
        .priority-urgent { background-color: #ffc107; color: #000; }
        .priority-normal { background-color: #28a745; color: white; }
        .priority-regulatory { background-color: #6f42c1; color: white; }
        .ai-section { background-color: #e7f3ff; padding: 15px; border-radius: 6px; margin: 15px 0; border-left: 3px solid #007bff; }
        .ai-section h4 { margin-top: 0; color: #0056b3; }
        .field { margin-bottom: 10px; }
        .field label { font-weight: bold; color: #6c757d; display: inline-block; min-width: 180px; }
        .field .value { color: #212529; }
        .fraud-score { font-size: 1.3em; font-weight: bold; }
        .fraud-high { color: #dc3545; }
        .fraud-medium { color: #ffc107; }
        .fraud-low { color: #28a745; }
        .decision-form { background-color: #f8f9fa; padding: 20px; border-radius: 6px; margin-top: 20px; border: 2px solid #dee2e6; }
        .decision-form h4 { margin-top: 0; color: #495057; }
        .form-group { margin-bottom: 15px; }
        .form-group label { display: block; font-weight: bold; margin-bottom: 5px; color: #495057; }
        .form-group input, .form-group select, .form-group textarea { width: 100%; padding: 10px; border: 1px solid #ced4da; border-radius: 4px; font-size: 14px; }
        .form-group textarea { height: 100px; resize: vertical; }
        .button-group { display: flex; gap: 10px; margin-top: 20px; }
        button { padding: 12px 24px; border: none; border-radius: 4px; cursor: pointer; font-weight: bold; font-size: 14px; transition: all 0.3s; }
        .btn-approve { background-color: #28a745; color: white; }
        .btn-approve:hover { background-color: #218838; }
        .btn-deny { background-color: #dc3545; color: white; }
        .btn-deny:hover { background-color: #c82333; }
        .btn-investigate { background-color: #ffc107; color: #000; }
        .btn-investigate:hover { background-color: #e0a800; }
        .empty-state { text-align: center; padding: 60px 20px; background-color: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .empty-state h3 { color: #6c757d; }
        .regulatory-warning { background-color: #fff3cd; border: 2px solid #ffc107; padding: 15px; border-radius: 6px; margin: 15px 0; }
        .regulatory-warning h4 { margin-top: 0; color: #856404; }
        .claim-summary { background-color: #f8f9fa; padding: 15px; border-radius: 6px; margin: 15px 0; }
        .amount { font-size: 1.4em; font-weight: bold; color: #28a745; }
        .risk-indicators { margin-top: 10px; }
        .risk-indicator { display: inline-block; background-color: #dc3545; color: white; padding: 4px 10px; border-radius: 12px; font-size: 12px; margin-right: 8px; margin-bottom: 8px; }
    </style>
    <script>
        function selectDecision(decision) {
            document.getElementById('decision_select').value = decision;
            if (decision === 'approve') {
                document.getElementById('settlement_amount_group').style.display = 'block';
            } else {
                document.getElementById('settlement_amount_group').style.display = 'none';
            }
        }
    </script>
</head>
<body>
    <div class="header">
        <h1>👨‍💼 Human Review Dashboard</h1>
        <p>Industry-Standard Claims Processing with Human Oversight</p>
    </div>

    <div class="nav">
        <a href="/">Submit Claim</a>
        <a href="/claims">View All Claims</a>
        <a href="/human-review">Human Review Queue</a>
    </div>

    <div class="role-selector">
        <label for="role_select"><strong>Your Role:</strong></label>
        <select id="role_select" onchange="window.location.href='/human-review?role=' + this.value">
            <option value="claims_adjuster" {{ 'selected' if role == 'claims_adjuster' else '' }}>Claims Adjuster</option>
            <option value="senior_adjuster" {{ 'selected' if role == 'senior_adjuster' else '' }}>Senior Adjuster</option>
            <option value="siu_investigator" {{ 'selected' if role == 'siu_investigator' else '' }}>SIU Investigator</option>
            <option value="underwriter" {{ 'selected' if role == 'underwriter' else '' }}>Underwriter</option>
            <option value="claims_supervisor" {{ 'selected' if role == 'claims_supervisor' else '' }}>Claims Supervisor</option>
        </select>
        <span style="margin-left: 20px; color: #6c757d;">{{ tasks|length }} pending tasks</span>
    </div>

    {% if tasks %}
        {% for task in tasks %}
        <div class="task-card {{ 'high-priority' if task.priority in ['high', 'urgent'] else '' }} {{ 'urgent' if task.priority == 'urgent' else '' }}">
            <div class="task-header">
                <div>
                    <div class="task-id">Task ID: {{ task.task_id }}</div>
                    <div style="font-size: 12px; color: #6c757d; margin-top: 5px;">Claim: {{ task.claim_id }}</div>
                </div>
                <span class="priority-badge priority-{{ task.priority }}">{{ task.priority }}</span>
            </div>

            <div class="claim-summary">
                <h4>📋 Claim Information</h4>
                <div class="field">
                    <label>Customer:</label>
                    <span class="value">{{ task.evidence_data.get('customer_name', 'N/A') }}</span>
                </div>
                <div class="field">
                    <label>Claim Type:</label>
                    <span class="value">{{ task.evidence_data.get('claim_type', 'N/A').title() }}</span>
                </div>
                <div class="field">
                    <label>Claim Amount:</label>
                    <span class="value amount">${{ "%.2f"|format(task.evidence_data.get('claim_amount', 0)) }}</span>
                </div>
                <div class="field">
                    <label>Description:</label>
                    <span class="value">{{ task.evidence_data.get('description', 'N/A') }}</span>
                </div>
            </div>

            {% if task.ai_recommendation %}
            <div class="ai-section">
                <h4>🤖 AI Analysis & Recommendation</h4>
                <div class="field">
                    <label>Fraud Score:</label>
                    <span class="value fraud-score {{ 'fraud-high' if task.ai_recommendation.get('fraud_score', 0) > 0.7 else 'fraud-medium' if task.ai_recommendation.get('fraud_score', 0) > 0.4 else 'fraud-low' }}">
                        {{ "%.2f"|format(task.ai_recommendation.get('fraud_score', 0)) }}
                    </span>
                </div>
                <div class="field">
                    <label>Policy Valid:</label>
                    <span class="value">{{ 'Yes' if task.ai_recommendation.get('policy_valid', True) else 'No' }}</span>
                </div>
                <div class="field">
                    <label>AI Recommendation:</label>
                    <span class="value">{{ task.ai_recommendation.get('recommended_reviewer', 'Review Required') }}</span>
                </div>
                {% if task.ai_recommendation.get('risk_factors') %}
                <div class="risk-indicators">
                    <label>Risk Factors:</label><br>
                    {% for factor in task.ai_recommendation.get('risk_factors', []) %}
                        <span class="risk-indicator">{{ factor }}</span>
                    {% endfor %}
                </div>
                {% endif %}
                <div style="margin-top: 10px; padding: 10px; background-color: white; border-radius: 4px; font-style: italic; color: #495057;">
                    <strong>Note:</strong> {{ task.ai_recommendation.get('compliance_note', 'Human decision required per industry standards') }}
                </div>
            </div>
            {% endif %}

            {% if task.regulatory_requirements %}
            <div class="regulatory-warning">
                <h4>⚖️ Regulatory Requirements</h4>
                <ul style="margin: 10px 0; padding-left: 20px;">
                    {% for req in task.regulatory_requirements %}
                        <li>{{ req.replace('_', ' ').title() }}</li>
                    {% endfor %}
                </ul>
                {% if task.regulatory_deadline %}
                <div style="margin-top: 10px;">
                    <strong>Regulatory Deadline:</strong> {{ task.regulatory_deadline }}
                </div>
                {% endif %}
            </div>
            {% endif %}

            <div class="decision-form">
                <h4>👨‍⚖️ Your Decision</h4>
                <form action="/submit-human-decision/{{ task.task_id }}" method="post">
                    <div class="form-group">
                        <label for="reviewer_id">Your ID / Name:</label>
                        <input type="text" id="reviewer_id" name="reviewer_id" required placeholder="e.g., adjuster_001 or John Smith">
                    </div>

                    <div class="form-group">
                        <label for="decision_select">Decision:</label>
                        <select id="decision_select" name="decision" required onchange="selectDecision(this.value)">
                            <option value="">-- Select Decision --</option>
                            <option value="approve">Approve Claim</option>
                            <option value="deny">Deny Claim</option>
                            <option value="investigate">Require Further Investigation</option>
                            <option value="escalate">Escalate to Supervisor</option>
                        </select>
                    </div>

                    <div class="form-group" id="settlement_amount_group" style="display: none;">
                        <label for="settlement_amount">Settlement Amount ($):</label>
                        <input type="number" id="settlement_amount" name="settlement_amount" step="0.01" min="0" placeholder="Enter settlement amount">
                    </div>

                    <div class="form-group">
                        <label for="reasoning">Reasoning / Notes:</label>
                        <textarea id="reasoning" name="reasoning" required placeholder="Provide detailed reasoning for your decision..."></textarea>
                    </div>

                    <div class="button-group">
                        <button type="button" class="btn-approve" onclick="selectDecision('approve'); this.closest('form').querySelector('[name=decision]').value='approve';">Quick Approve</button>
                        <button type="button" class="btn-deny" onclick="selectDecision('deny'); this.closest('form').querySelector('[name=decision]').value='deny';">Quick Deny</button>
                        <button type="button" class="btn-investigate" onclick="selectDecision('investigate'); this.closest('form').querySelector('[name=decision]').value='investigate';">Investigate</button>
                        <button type="submit" style="background-color: #007bff; color: white; margin-left: auto;">Submit Decision</button>
                    </div>
                </form>
            </div>
        </div>
        {% endfor %}
    {% else %}
        <div class="empty-state">
            <h3>✅ No Pending Tasks</h3>
            <p>All claims for {{ role.replace('_', ' ').title() }} have been reviewed.</p>
            <p><a href="/claims">View All Claims</a></p>
        </div>
    {% endif %}
</body>
</html>
"""

# Write template files synchronously
def create_template_files():
    """Create template files"""
    templates_dir = os.path.join(os.path.dirname(__file__), "templates")
    os.makedirs(templates_dir, exist_ok=True)

    with open(os.path.join(templates_dir, "claim_form.html"), "w") as f:
        f.write(claim_form_html)

    with open(os.path.join(templates_dir, "claims_list.html"), "w") as f:
        f.write(claims_list_html)

    with open(os.path.join(templates_dir, "claim_detail.html"), "w") as f:
        f.write(claim_detail_html)

    with open(os.path.join(templates_dir, "human_review.html"), "w") as f:
        f.write(human_review_html)

# Create templates on import
create_template_files()