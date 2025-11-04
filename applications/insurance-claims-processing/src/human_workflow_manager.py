"""
Human Workflow Management System
Industry-standard claims processing with proper human oversight and regulatory compliance
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, TypedDict, Literal
from enum import Enum
from dataclasses import dataclass, asdict
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Industry-standard roles and authority levels
class ClaimsRole(str, Enum):
    FNOL_SPECIALIST = "fnol_specialist"           # First Notice of Loss intake
    CLAIMS_ADJUSTER = "claims_adjuster"           # Licensed field adjusters
    SENIOR_ADJUSTER = "senior_adjuster"           # Senior adjusters for complex claims
    UNDERWRITER = "underwriter"                   # Policy coverage decisions
    SENIOR_UNDERWRITER = "senior_underwriter"     # Complex coverage decisions
    SIU_INVESTIGATOR = "siu_investigator"         # Special Investigation Unit
    CLAIMS_SUPERVISOR = "claims_supervisor"       # Supervisory approval
    CLAIMS_MANAGER = "claims_manager"             # Management oversight
    LEGAL_COUNSEL = "legal_counsel"               # Legal review for liability

class TaskStatus(str, Enum):
    PENDING_HUMAN_REVIEW = "pending_human_review"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    DENIED = "denied"
    ESCALATED = "escalated"
    REQUIRES_ADDITIONAL_INFO = "requires_additional_info"
    SUSPENDED = "suspended"

class TaskPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"
    REGULATORY = "regulatory"  # Regulatory deadline driven

@dataclass
class ReservedAuthority:
    """Industry-standard reserved authority limits for different roles"""
    role: ClaimsRole
    max_settlement_amount: float
    max_reserve_amount: float
    can_deny_claims: bool
    can_approve_coverage: bool
    requires_supervisor_approval: bool
    regulatory_reporting_required: bool

@dataclass
class HumanTask:
    """Human workflow task with industry compliance requirements"""
    task_id: str
    claim_id: str
    task_type: str
    assigned_role: ClaimsRole
    assigned_to: Optional[str]  # Specific person if assigned
    priority: TaskPriority
    status: TaskStatus
    created_at: datetime
    due_date: datetime
    regulatory_deadline: Optional[datetime]

    # Task details
    description: str
    ai_recommendation: Dict[str, Any]
    evidence_data: Dict[str, Any]
    regulatory_requirements: List[str]

    # Audit trail
    audit_trail: List[Dict[str, Any]]

    # Industry compliance
    requires_license_verification: bool
    regulatory_jurisdiction: str  # State/province
    bad_faith_prevention_notes: str

class HumanWorkflowManager:
    """
    Manages human-in-the-loop workflows for insurance claims processing
    Ensures compliance with industry standards and regulatory requirements
    """

    def __init__(self):
        self.manager_id = "human_workflow_001"

        # Define reserved authority levels per industry standards
        self.authority_levels = {
            ClaimsRole.FNOL_SPECIALIST: ReservedAuthority(
                role=ClaimsRole.FNOL_SPECIALIST,
                max_settlement_amount=0.0,  # No settlement authority
                max_reserve_amount=5000.0,  # Can set initial reserves
                can_deny_claims=False,
                can_approve_coverage=False,
                requires_supervisor_approval=True,
                regulatory_reporting_required=False
            ),
            ClaimsRole.CLAIMS_ADJUSTER: ReservedAuthority(
                role=ClaimsRole.CLAIMS_ADJUSTER,
                max_settlement_amount=10000.0,
                max_reserve_amount=25000.0,
                can_deny_claims=True,
                can_approve_coverage=False,  # Underwriter required
                requires_supervisor_approval=False,
                regulatory_reporting_required=True
            ),
            ClaimsRole.SENIOR_ADJUSTER: ReservedAuthority(
                role=ClaimsRole.SENIOR_ADJUSTER,
                max_settlement_amount=50000.0,
                max_reserve_amount=100000.0,
                can_deny_claims=True,
                can_approve_coverage=False,
                requires_supervisor_approval=False,
                regulatory_reporting_required=True
            ),
            ClaimsRole.UNDERWRITER: ReservedAuthority(
                role=ClaimsRole.UNDERWRITER,
                max_settlement_amount=0.0,  # No settlement authority
                max_reserve_amount=0.0,
                can_deny_claims=True,  # Can deny for coverage
                can_approve_coverage=True,
                requires_supervisor_approval=False,
                regulatory_reporting_required=True
            ),
            ClaimsRole.SIU_INVESTIGATOR: ReservedAuthority(
                role=ClaimsRole.SIU_INVESTIGATOR,
                max_settlement_amount=0.0,
                max_reserve_amount=0.0,
                can_deny_claims=True,  # Can recommend denial for fraud
                can_approve_coverage=False,
                requires_supervisor_approval=False,
                regulatory_reporting_required=True
            ),
            ClaimsRole.CLAIMS_SUPERVISOR: ReservedAuthority(
                role=ClaimsRole.CLAIMS_SUPERVISOR,
                max_settlement_amount=100000.0,
                max_reserve_amount=250000.0,
                can_deny_claims=True,
                can_approve_coverage=True,
                requires_supervisor_approval=False,
                regulatory_reporting_required=True
            ),
            ClaimsRole.CLAIMS_MANAGER: ReservedAuthority(
                role=ClaimsRole.CLAIMS_MANAGER,
                max_settlement_amount=500000.0,
                max_reserve_amount=1000000.0,
                can_deny_claims=True,
                can_approve_coverage=True,
                requires_supervisor_approval=False,
                regulatory_reporting_required=True
            )
        }

        # Active human tasks
        self.active_tasks: Dict[str, HumanTask] = {}

        # Regulatory compliance tracking
        self.regulatory_deadlines = {
            "initial_contact": timedelta(days=1),      # Contact claimant within 24 hours
            "coverage_decision": timedelta(days=30),   # Coverage decision within 30 days
            "settlement_offer": timedelta(days=45),    # Settlement offer timeframe
            "claim_resolution": timedelta(days=90),    # Total resolution timeframe
            "fraud_reporting": timedelta(days=10)      # Report suspected fraud
        }

        logger.info(f"Initialized Human Workflow Manager: {self.manager_id}")

    async def route_ai_decision_to_human(
        self,
        claim_data: Dict[str, Any],
        ai_recommendation: Dict[str, Any],
        decision_type: str
    ) -> Dict[str, Any]:
        """
        Route AI decisions to appropriate human roles based on industry standards
        This replaces autonomous AI decision-making with human oversight
        """

        claim_amount = claim_data.get("claim_amount", 0)
        fraud_score = ai_recommendation.get("fraud_score", 0.0)
        policy_issues = ai_recommendation.get("policy_issues", [])

        # Determine required human role based on industry standards
        required_role, priority, regulatory_requirements = self._determine_human_assignment(
            claim_amount, fraud_score, policy_issues, decision_type
        )

        # Create human task
        task = await self._create_human_task(
            claim_data=claim_data,
            ai_recommendation=ai_recommendation,
            decision_type=decision_type,
            required_role=required_role,
            priority=priority,
            regulatory_requirements=regulatory_requirements
        )

        return {
            "decision_type": "ROUTED_TO_HUMAN",
            "ai_recommendation": ai_recommendation,
            "human_task": asdict(task),
            "required_role": required_role.value,
            "priority": priority.value,
            "regulatory_deadline": task.regulatory_deadline.isoformat() if task.regulatory_deadline else None,
            "message": f"Claim routed to {required_role.value} for human review as required by industry standards",
            "compliance_note": "AI assistance provided - Human decision required for regulatory compliance"
        }

    def _determine_human_assignment(
        self,
        claim_amount: float,
        fraud_score: float,
        policy_issues: List[str],
        decision_type: str
    ) -> tuple[ClaimsRole, TaskPriority, List[str]]:
        """Determine appropriate human role based on industry standards"""

        regulatory_requirements = []

        # Fraud threshold triggers - SIU required
        if fraud_score > 0.7:
            return (
                ClaimsRole.SIU_INVESTIGATOR,
                TaskPriority.HIGH,
                ["fraud_investigation_required", "siu_licensed_investigator"]
            )

        # High-value claims - Senior adjuster required
        if claim_amount > 100000:
            regulatory_requirements.extend(["large_loss_reporting", "senior_adjuster_review"])
            return (
                ClaimsRole.SENIOR_ADJUSTER,
                TaskPriority.HIGH,
                regulatory_requirements
            )

        # Policy coverage issues - Underwriter required
        if policy_issues or decision_type == "coverage_decision":
            regulatory_requirements.extend(["coverage_analysis", "underwriter_interpretation"])
            return (
                ClaimsRole.UNDERWRITER,
                TaskPriority.NORMAL,
                regulatory_requirements
            )

        # Medium value claims - Regular adjuster
        if claim_amount > 10000:
            regulatory_requirements.append("adjuster_investigation")
            return (
                ClaimsRole.CLAIMS_ADJUSTER,
                TaskPriority.NORMAL,
                regulatory_requirements
            )

        # Low value claims - Still require adjuster (industry standard)
        regulatory_requirements.append("basic_adjuster_review")
        return (
            ClaimsRole.CLAIMS_ADJUSTER,
            TaskPriority.LOW,
            regulatory_requirements
        )

    async def _create_human_task(
        self,
        claim_data: Dict[str, Any],
        ai_recommendation: Dict[str, Any],
        decision_type: str,
        required_role: ClaimsRole,
        priority: TaskPriority,
        regulatory_requirements: List[str]
    ) -> HumanTask:
        """Create a human workflow task with proper compliance tracking"""

        task_id = f"HT-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{claim_data.get('claim_id', 'UNKNOWN')}"
        claim_id = claim_data.get("claim_id", "")

        # Calculate regulatory deadlines
        now = datetime.utcnow()
        due_date = now + timedelta(days=3)  # Standard 3-day SLA
        regulatory_deadline = None

        if decision_type == "coverage_decision":
            regulatory_deadline = now + self.regulatory_deadlines["coverage_decision"]
        elif "fraud" in decision_type.lower():
            regulatory_deadline = now + self.regulatory_deadlines["fraud_reporting"]

        # Create initial audit entry
        initial_audit = {
            "timestamp": now.isoformat(),
            "action": "task_created",
            "actor": "ai_system",
            "details": f"AI recommendation routed to {required_role.value}",
            "ai_confidence": ai_recommendation.get("confidence", 0.0)
        }

        task = HumanTask(
            task_id=task_id,
            claim_id=claim_id,
            task_type=decision_type,
            assigned_role=required_role,
            assigned_to=None,
            priority=priority,
            status=TaskStatus.PENDING_HUMAN_REVIEW,
            created_at=now,
            due_date=due_date,
            regulatory_deadline=regulatory_deadline,
            description=f"Human review required for {decision_type}",
            ai_recommendation=ai_recommendation,
            evidence_data=claim_data,
            regulatory_requirements=regulatory_requirements,
            audit_trail=[initial_audit],
            requires_license_verification=required_role in [
                ClaimsRole.CLAIMS_ADJUSTER,
                ClaimsRole.SENIOR_ADJUSTER,
                ClaimsRole.SIU_INVESTIGATOR
            ],
            regulatory_jurisdiction=claim_data.get("jurisdiction", "STATE_UNKNOWN"),
            bad_faith_prevention_notes=""
        )

        # Store active task
        self.active_tasks[task_id] = task

        return task

    async def submit_human_decision(
        self,
        task_id: str,
        human_decision: Dict[str, Any],
        reviewer_id: str,
        reviewer_license: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Submit human decision with proper authority validation and audit trail
        """

        if task_id not in self.active_tasks:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

        task = self.active_tasks[task_id]

        # Validate reviewer authority
        authority_check = self._validate_reviewer_authority(task, human_decision, reviewer_id)
        if not authority_check["authorized"]:
            return {
                "status": "AUTHORITY_VIOLATION",
                "message": authority_check["reason"],
                "required_role": task.assigned_role.value,
                "escalation_required": True
            }

        # License verification for regulated roles
        if task.requires_license_verification and not reviewer_license:
            return {
                "status": "LICENSE_VERIFICATION_REQUIRED",
                "message": f"License verification required for {task.assigned_role.value}",
                "regulatory_requirement": True
            }

        # Update task with human decision
        decision_audit = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": "human_decision_submitted",
            "actor": reviewer_id,
            "license": reviewer_license,
            "decision": human_decision.get("decision"),
            "reasoning": human_decision.get("reasoning", ""),
            "authority_level": task.assigned_role.value
        }

        task.audit_trail.append(decision_audit)
        task.status = TaskStatus.APPROVED if human_decision.get("decision") == "approve" else TaskStatus.DENIED

        # Check if escalation is needed
        escalation_needed = self._check_escalation_requirements(task, human_decision)

        result = {
            "task_id": task_id,
            "status": "HUMAN_DECISION_RECORDED",
            "decision": human_decision,
            "reviewer": reviewer_id,
            "authority_level": task.assigned_role.value,
            "regulatory_compliant": True,
            "audit_trail_updated": True,
            "escalation_needed": escalation_needed
        }

        if escalation_needed:
            escalation_task = await self._escalate_task(task, human_decision)
            result["escalation_task"] = asdict(escalation_task)

        return result

    def _validate_reviewer_authority(
        self,
        task: HumanTask,
        decision: Dict[str, Any],
        reviewer_id: str
    ) -> Dict[str, Any]:
        """Validate if reviewer has authority for this decision"""

        authority = self.authority_levels[task.assigned_role]
        decision_type = decision.get("decision")
        amount = decision.get("settlement_amount", 0)

        # Check settlement authority
        if decision_type == "settle" and amount > authority.max_settlement_amount:
            return {
                "authorized": False,
                "reason": f"Settlement amount ${amount} exceeds authority limit ${authority.max_settlement_amount}"
            }

        # Check denial authority
        if decision_type == "deny" and not authority.can_deny_claims:
            return {
                "authorized": False,
                "reason": f"Role {task.assigned_role.value} cannot deny claims"
            }

        # Check coverage authority
        if decision_type == "coverage_approve" and not authority.can_approve_coverage:
            return {
                "authorized": False,
                "reason": f"Role {task.assigned_role.value} cannot approve coverage - Underwriter required"
            }

        return {"authorized": True, "reason": "Authority validated"}

    def _check_escalation_requirements(
        self,
        task: HumanTask,
        decision: Dict[str, Any]
    ) -> bool:
        """Check if decision requires escalation to higher authority"""

        authority = self.authority_levels[task.assigned_role]

        # Always escalate if role requires supervisor approval
        if authority.requires_supervisor_approval:
            return True

        # Escalate high-value settlements
        settlement_amount = decision.get("settlement_amount", 0)
        if settlement_amount > authority.max_settlement_amount * 0.8:  # 80% of authority
            return True

        # Escalate fraud denials for additional review
        if decision.get("decision") == "deny" and "fraud" in decision.get("reasoning", "").lower():
            return True

        return False

    async def _escalate_task(
        self,
        original_task: HumanTask,
        human_decision: Dict[str, Any]
    ) -> HumanTask:
        """Escalate task to higher authority"""

        # Determine escalation role
        escalation_role = self._get_escalation_role(original_task.assigned_role)

        escalated_task = await self._create_human_task(
            claim_data=original_task.evidence_data,
            ai_recommendation=original_task.ai_recommendation,
            decision_type=f"escalated_{original_task.task_type}",
            required_role=escalation_role,
            priority=TaskPriority.HIGH,
            regulatory_requirements=original_task.regulatory_requirements + ["escalation_review"]
        )

        # Link to original task
        escalated_task.audit_trail.append({
            "timestamp": datetime.utcnow().isoformat(),
            "action": "escalated_from_task",
            "original_task": original_task.task_id,
            "escalation_reason": "Authority limit or policy requirement",
            "original_decision": human_decision
        })

        return escalated_task

    def _get_escalation_role(self, current_role: ClaimsRole) -> ClaimsRole:
        """Get the appropriate escalation role"""

        escalation_map = {
            ClaimsRole.FNOL_SPECIALIST: ClaimsRole.CLAIMS_ADJUSTER,
            ClaimsRole.CLAIMS_ADJUSTER: ClaimsRole.SENIOR_ADJUSTER,
            ClaimsRole.SENIOR_ADJUSTER: ClaimsRole.CLAIMS_SUPERVISOR,
            ClaimsRole.UNDERWRITER: ClaimsRole.SENIOR_UNDERWRITER,
            ClaimsRole.SENIOR_UNDERWRITER: ClaimsRole.CLAIMS_MANAGER,
            ClaimsRole.SIU_INVESTIGATOR: ClaimsRole.CLAIMS_SUPERVISOR,
            ClaimsRole.CLAIMS_SUPERVISOR: ClaimsRole.CLAIMS_MANAGER
        }

        return escalation_map.get(current_role, ClaimsRole.CLAIMS_MANAGER)

    def get_pending_tasks_by_role(self, role: ClaimsRole) -> List[Dict[str, Any]]:
        """Get all pending tasks for a specific role"""

        pending_tasks = [
            asdict(task) for task in self.active_tasks.values()
            if task.assigned_role == role and task.status == TaskStatus.PENDING_HUMAN_REVIEW
        ]

        # Sort by priority and due date
        pending_tasks.sort(key=lambda x: (
            x["priority"] == TaskPriority.REGULATORY.value,
            x["priority"] == TaskPriority.URGENT.value,
            x["priority"] == TaskPriority.HIGH.value,
            x["due_date"]
        ), reverse=True)

        return pending_tasks

    def get_regulatory_compliance_status(self) -> Dict[str, Any]:
        """Get regulatory compliance status for all active tasks"""

        now = datetime.utcnow()
        overdue_tasks = []
        approaching_deadline = []

        for task in self.active_tasks.values():
            if task.regulatory_deadline:
                time_remaining = task.regulatory_deadline - now

                if time_remaining.total_seconds() < 0:
                    overdue_tasks.append(task.task_id)
                elif time_remaining.total_seconds() < 86400:  # 24 hours
                    approaching_deadline.append(task.task_id)

        return {
            "total_active_tasks": len(self.active_tasks),
            "overdue_regulatory_tasks": len(overdue_tasks),
            "approaching_deadline": len(approaching_deadline),
            "overdue_task_ids": overdue_tasks,
            "deadline_approaching": approaching_deadline,
            "compliance_status": "NON_COMPLIANT" if overdue_tasks else "COMPLIANT"
        }

# FastAPI Application for Human Workflow Management
app = FastAPI(
    title="Human Workflow Management System",
    description="Industry-standard claims processing with human oversight and regulatory compliance",
    version="1.0.0"
)

# Global workflow manager instance
workflow_manager: Optional[HumanWorkflowManager] = None

@app.on_event("startup")
async def startup_event():
    global workflow_manager
    workflow_manager = HumanWorkflowManager()
    logger.info("Human Workflow Management System started")

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "human-workflow-manager",
        "capabilities": [
            "human_task_routing",
            "authority_validation",
            "regulatory_compliance",
            "audit_trail_management",
            "escalation_handling"
        ],
        "compliance_focus": "industry_standard_claims_processing",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/route-decision")
async def route_ai_decision_to_human(
    claim_data: Dict[str, Any],
    ai_recommendation: Dict[str, Any],
    decision_type: str
):
    """Route AI decision to appropriate human role"""
    if not workflow_manager:
        raise HTTPException(status_code=503, detail="Workflow manager not initialized")

    result = await workflow_manager.route_ai_decision_to_human(
        claim_data, ai_recommendation, decision_type
    )
    return result

@app.post("/submit-decision/{task_id}")
async def submit_human_decision(
    task_id: str,
    human_decision: Dict[str, Any],
    reviewer_id: str,
    reviewer_license: Optional[str] = None
):
    """Submit human decision for a task"""
    if not workflow_manager:
        raise HTTPException(status_code=503, detail="Workflow manager not initialized")

    result = await workflow_manager.submit_human_decision(
        task_id, human_decision, reviewer_id, reviewer_license
    )
    return result

@app.get("/tasks/{role}")
async def get_pending_tasks(role: str):
    """Get pending tasks for a specific role"""
    if not workflow_manager:
        raise HTTPException(status_code=503, detail="Workflow manager not initialized")

    try:
        claims_role = ClaimsRole(role)
        tasks = workflow_manager.get_pending_tasks_by_role(claims_role)
        return {"role": role, "pending_tasks": tasks, "count": len(tasks)}
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid role: {role}")

@app.get("/compliance-status")
async def get_compliance_status():
    """Get regulatory compliance status"""
    if not workflow_manager:
        raise HTTPException(status_code=503, detail="Workflow manager not initialized")

    status = workflow_manager.get_regulatory_compliance_status()
    return status

@app.get("/authority-levels")
async def get_authority_levels():
    """Get reserved authority levels for all roles"""
    if not workflow_manager:
        raise HTTPException(status_code=503, detail="Workflow manager not initialized")

    return {
        role.value: asdict(authority)
        for role, authority in workflow_manager.authority_levels.items()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)