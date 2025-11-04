"""
Enhanced Database Models for Production-Grade Insurance Claims Processing
Based on industry-standard insurance data schemas
"""

from datetime import datetime, date
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum

# Enums for standardized values
class PolicyStatus(str, Enum):
    QUOTE = "Quote"
    ISSUED = "Issued"
    ACTIVE = "Active"
    LAPSED = "Lapsed"
    CANCELLED = "Cancelled"
    TERMINATED = "Terminated"

class ClaimStatus(str, Enum):
    RECEIVED = "Received"
    IN_PROGRESS = "In Progress"
    UNDER_INVESTIGATION = "Under Investigation"
    ADJUDICATED = "Adjudicated"
    APPROVED = "Approved"
    DENIED = "Denied"
    PAID = "Paid"
    CLOSED = "Closed"

class LineOfBusiness(str, Enum):
    AUTO_PERSONAL = "Personal Auto"
    AUTO_COMMERCIAL = "Commercial Auto"
    WORKERS_COMP = "Workers Compensation"
    GENERAL_LIABILITY = "General Liability"
    PROPERTY = "Property"
    LIFE = "Life Insurance"
    HEALTH = "Health Insurance"

class ClaimType(str, Enum):
    COLLISION = "Collision"
    COMPREHENSIVE = "Comprehensive"
    LIABILITY = "Liability"
    PROPERTY_DAMAGE = "Property Damage"
    BODILY_INJURY = "Bodily Injury"
    THEFT = "Theft"
    VANDALISM = "Vandalism"
    FIRE = "Fire"
    WEATHER = "Weather Damage"
    DEATH_BENEFIT = "Death Benefit"

class AdjudicationStatus(str, Enum):
    PENDING = "Pending"
    AWAITING_DOCUMENTS = "Awaiting Documents"
    FRAUD_INVESTIGATION = "Fraud Investigation In Progress"
    MEDICAL_REVIEW = "Medical Review"
    LEGAL_REVIEW = "Legal Review"
    READY_FOR_PAYMENT = "Ready for Payment"
    COMPLETED = "Completed"

# Enhanced Policy Model
class PolicyModel(BaseModel):
    """Production-grade policy model"""
    # Policy Identification
    policy_number: str = Field(..., description="Unique policy number")
    policy_version: int = Field(default=1, description="Policy version number")
    quote_number: Optional[str] = Field(None, description="Original quote number")

    # Policy Dates
    quote_generation_date: Optional[datetime] = None
    quote_expiration_date: Optional[datetime] = None
    policy_effective_date: date
    policy_expiration_date: date
    policy_issue_date: date
    policy_termination_date: Optional[date] = None

    # Policy Details
    line_of_business: LineOfBusiness
    lob_code: str = Field(..., description="Line of business code")
    policy_status: PolicyStatus
    policy_status_reason: Optional[str] = None
    new_renewal: str = Field(..., description="N for new, R for renewal")

    # Coverage
    policy_term: int = Field(..., description="Policy term in years")
    sum_assured: Optional[float] = Field(None, description="Total coverage amount")
    policy_value: Optional[float] = Field(None, description="Policy cash value")
    coverage_type: Optional[str] = None
    no_of_coverage_units: Optional[int] = None

    # Premium Information
    policy_premium: float = Field(..., description="Total annual premium")
    yearly_premium: Optional[float] = None
    monthly_premium: Optional[float] = None
    premium_paying_term: Optional[int] = None
    premium_paid_till_date: float = Field(default=0.0)
    next_action_date: Optional[date] = None
    month_anniversary_date: Optional[int] = None

    # Endorsements
    endorsement_change: bool = Field(default=False)
    endorsement_change_type: Optional[str] = None

    # Customer Information
    primary_insured_customer_id: str
    customer_no: str

    # Agent/Producer Information
    sales_channel: str
    sales_agency_code: Optional[str] = None
    sales_agent_code: str
    servicing_agent_code: Optional[str] = None
    producer: Optional[str] = None
    commission_paid_till_date: float = Field(default=0.0)

    # Geographic Information
    issue_state: str
    resident_state: str
    issue_age: int
    city: Optional[str] = None
    territory: Optional[str] = None

    # Business Attributes (for commercial policies)
    industry: Optional[str] = None
    sector: Optional[str] = None
    num_employees: Optional[int] = None
    employee_size_tier: Optional[str] = None
    revenue: Optional[float] = None

    # Risk Assessment
    underwriting_class: Optional[str] = None
    smoking_class: Optional[str] = None

    # Address
    policy_correspondence_address: Optional[Dict[str, str]] = None

    # Riders (for life insurance)
    riders: List[Dict[str, Any]] = Field(default_factory=list)

    # Metadata
    policy_notes: Optional[str] = None
    policy_in_force: bool = Field(default=True)
    policy_expiring: bool = Field(default=False)
    generation_date: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True

# Enhanced Claim Model
class ClaimModel(BaseModel):
    """Production-grade claim model"""
    # Claim Identification
    claim_id: str = Field(..., description="Unique claim ID (Claim No)")
    claim_number: Optional[str] = None  # Alternative claim number
    policy_id: str = Field(..., description="Associated policy number")

    # Claim Dates
    time_of_loss: Optional[datetime] = None
    incident_date: datetime = Field(..., description="Date of incident/loss")
    loss_reported_on: datetime = Field(default_factory=datetime.utcnow)
    claims_reported_date: datetime = Field(default_factory=datetime.utcnow)
    adjudication_date: Optional[datetime] = None
    payment_date: Optional[datetime] = None

    # Claim Status
    claim_status: ClaimStatus
    claim_description: Optional[str] = None
    adjudication_status: AdjudicationStatus = Field(default=AdjudicationStatus.PENDING)
    adjudication_description: Optional[str] = None

    # Claim Type and Description
    claim_type: ClaimType
    description_of_loss: str = Field(..., description="Detailed description of loss")

    # Loss Location
    location_of_loss: Optional[Dict[str, str]] = None
    loss_address_line_1: Optional[str] = None
    loss_address_line_2: Optional[str] = None
    loss_zip_code: Optional[str] = None
    loss_state: Optional[str] = None

    # Claimant Information
    claimant_first_name: str
    claimant_last_name: str
    claimant_customer_id: Optional[str] = None
    claimant_phone_number: Optional[str] = None
    claimant_email: Optional[str] = None
    claimant_address: Optional[Dict[str, str]] = None

    # Relationship
    relationship_to_primary_insured: str = Field(default="Self")

    # Affected Parties
    affected_parties: List[Dict[str, Any]] = Field(default_factory=list)

    # Financial Information
    total_adjudicated_claim_amount: Optional[float] = None
    claim_settlement_expense: Optional[float] = None
    total_claim_settlement_amount: Optional[float] = None
    claimed_amount: float = Field(..., description="Initial claim amount")
    approved_amount: Optional[float] = None
    paid_amount: Optional[float] = None

    # Benefit Information (for life insurance)
    benefit_code: Optional[List[str]] = Field(default_factory=list)
    benefit_amount: Optional[float] = None

    # Documents
    eob_generated: bool = Field(default=False, description="Explanation of Benefits generated")
    requirement_raised: bool = Field(default=False)
    document_received: List[str] = Field(default_factory=list)

    # Payment Details
    payment_detail: Optional[Dict[str, Any]] = None
    payment_type: Optional[str] = None  # Check/Bank Transfer
    bank_name: Optional[str] = None
    check_number: Optional[str] = None
    routing_number: Optional[str] = None
    account_number: Optional[str] = None
    check_payment_status: Optional[str] = None

    # Beneficiary Information (for death claims)
    beneficiary_name: Optional[str] = None
    beneficiary_relationship: Optional[str] = None
    beneficiary_pct: Optional[int] = None

    # AI and Agentic Analysis
    fraud_score: Optional[float] = Field(None, description="AI fraud detection score")
    ai_recommendation: Optional[Dict[str, Any]] = None
    external_data_analysis: Optional[Dict[str, Any]] = None
    risk_indicators: List[str] = Field(default_factory=list)
    agentic_insights: List[str] = Field(default_factory=list)

    # Assignment and Workflow
    assigned_adjuster: Optional[str] = None
    assigned_adjuster_license: Optional[str] = None
    current_stage: str = Field(default="initial_review")
    priority: str = Field(default="normal")  # low, normal, high, urgent

    # Human Decision
    human_decision: Optional[Dict[str, Any]] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    reviewer_license: Optional[str] = None

    # Audit Trail
    processing_history: List[Dict[str, Any]] = Field(default_factory=list)
    status_history: List[Dict[str, Any]] = Field(default_factory=list)

    # Metadata
    policy_effective_date: Optional[date] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True

# Customer/Insured Model
class CustomerModel(BaseModel):
    """Production-grade customer model"""
    # Customer Identification
    customer_id: str = Field(..., description="Unique customer ID")
    party_id: Optional[str] = None
    party_type: str = Field(default="IND", description="IND for individual, ORG for organization")
    national_id: Optional[str] = None  # SSN or EIN

    # Personal Information (for individuals)
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    sex: Optional[str] = None
    date_of_birth: Optional[date] = None
    age: Optional[int] = None
    marital_status: Optional[str] = None
    deceased: bool = Field(default=False)
    date_of_death: Optional[date] = None

    # Organization Information (for organizations)
    organization_name: Optional[str] = None
    organization_type: Optional[str] = None  # Commercial/Private
    sic_code: Optional[str] = None

    # Contact Information
    email: str
    phone_number: Optional[str] = None
    phone_type: Optional[str] = None

    # Address
    address: Optional[Dict[str, str]] = None
    city: Optional[str] = None
    state: str
    zip_code: Optional[str] = None
    country: str = Field(default="USA")

    # Organization Contacts (for business customers)
    org_phone: Optional[List[str]] = Field(default_factory=list)
    org_email: Optional[List[Dict[str, str]]] = Field(default_factory=list)
    org_address: Optional[List[Dict[str, Any]]] = Field(default_factory=list)

    # Policies
    policies: List[str] = Field(default_factory=list)

    # Dependents
    dependents: List[Dict[str, Any]] = Field(default_factory=list)

    # Billing Information
    billing_account_number: Optional[str] = None
    payment_methods: List[Dict[str, Any]] = Field(default_factory=list)

    # Relationships
    relationships: List[Dict[str, Any]] = Field(default_factory=list)

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True

# Beneficiary Model (for life insurance)
class BeneficiaryModel(BaseModel):
    """Beneficiary information for life insurance policies"""
    policy_number: str
    customer_id: str

    # Primary Beneficiary
    beneficiary_name: str
    beneficiary_dob: Optional[date] = None
    beneficiary_age: Optional[int] = None
    beneficiary_relation: str
    beneficiary_pct: int = Field(default=100)

    # Contingent Beneficiary
    contingent_beneficiaries: List[Dict[str, Any]] = Field(default_factory=list)

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# Producer/Agent Model
class ProducerModel(BaseModel):
    """Insurance agent/producer model"""
    producer_code: str = Field(..., description="Unique producer code")
    producer_name: str
    agency_name: Optional[str] = None

    # License Information
    state: str
    license_number: Optional[str] = None
    license_states: List[str] = Field(default_factory=list)

    # Contact
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[Dict[str, str]] = None

    # Performance
    policies_in_force: int = Field(default=0)
    total_premium: float = Field(default=0.0)

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# Task Model for Human-in-the-Loop Workflows
class HumanTaskModel(BaseModel):
    """Human review task model"""
    task_id: str
    claim_id: str
    policy_id: str

    # Task Details
    task_type: str  # claim_review, fraud_investigation, settlement_approval, etc.
    title: str
    description: str
    priority: str = Field(default="normal")

    # Assignment
    assigned_to: str  # Role or specific user
    assigned_role: str  # claims_adjuster, siu_investigator, supervisor, etc.

    # Evidence and Context
    evidence_data: Dict[str, Any] = Field(default_factory=dict)
    ai_recommendation: Optional[Dict[str, Any]] = None
    regulatory_requirements: List[str] = Field(default_factory=list)
    regulatory_deadline: Optional[datetime] = None

    # Status
    status: str = Field(default="pending")  # pending, in_progress, completed, cancelled

    # Decision
    decision: Optional[Dict[str, Any]] = None
    reviewer_id: Optional[str] = None
    reviewer_license: Optional[str] = None

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    due_date: Optional[datetime] = None

    class Config:
        use_enum_values = True
