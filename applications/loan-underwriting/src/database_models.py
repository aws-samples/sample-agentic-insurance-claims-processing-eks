"""
Database Models for Intelligent Loan Underwriting System
Defines data structures for loan applications, borrowers, and underwriting decisions
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
from pydantic import BaseModel, Field
from bson import ObjectId


class PyObjectId(str):
    """Custom ObjectId type for Pydantic v2"""
    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type, _handler):
        from pydantic_core import core_schema

        def validate(value):
            if not ObjectId.is_valid(value):
                raise ValueError("Invalid ObjectId")
            return str(ObjectId(value))

        return core_schema.with_info_plain_validator_function(
            validate,
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda x: str(x)
            )
        )

    @classmethod
    def __get_pydantic_json_schema__(cls, schema, handler):
        return {'type': 'string'}


class LoanType(str, Enum):
    """Loan product types"""
    PERSONAL = "personal"
    AUTO = "auto"
    MORTGAGE = "mortgage"
    BUSINESS = "business"
    STUDENT = "student"
    HOME_EQUITY = "home_equity"


class LoanStatus(str, Enum):
    """Loan application status"""
    SUBMITTED = "submitted"
    DOCUMENT_REVIEW = "document_review"
    UNDERWRITING = "underwriting"
    APPROVED = "approved"
    CONDITIONALLY_APPROVED = "conditionally_approved"
    DENIED = "denied"
    WITHDRAWN = "withdrawn"
    FUNDED = "funded"


class EmploymentType(str, Enum):
    """Employment status types"""
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    SELF_EMPLOYED = "self_employed"
    CONTRACT = "contract"
    RETIRED = "retired"
    UNEMPLOYED = "unemployed"


class RiskLevel(str, Enum):
    """Risk assessment levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


# ============================================================================
# Core Data Models
# ============================================================================

class Address(BaseModel):
    """Physical address"""
    street: str
    city: str
    state: str
    zip_code: str
    country: str = "USA"
    residence_type: str = Field(default="own", description="own, rent, other")
    years_at_address: float = 0.0


class Employment(BaseModel):
    """Employment information"""
    employer_name: str
    employment_type: EmploymentType
    job_title: str
    years_employed: float
    monthly_income: float
    employer_phone: Optional[str] = None
    employer_address: Optional[Address] = None
    previous_employment: Optional[List[Dict]] = []


class FinancialInformation(BaseModel):
    """Borrower financial details"""
    annual_income: float
    monthly_income: float
    other_income: float = 0.0
    monthly_debts: float = 0.0
    credit_score: Optional[int] = None
    assets: Dict[str, float] = Field(default_factory=dict)  # checking, savings, investments
    liabilities: Dict[str, float] = Field(default_factory=dict)  # credit cards, loans, etc.
    bankruptcy_history: bool = False
    foreclosure_history: bool = False


class Document(BaseModel):
    """Uploaded document metadata"""
    document_id: str = Field(default_factory=lambda: str(ObjectId()))
    document_type: str  # paystub, w2, bank_statement, tax_return, id, etc.
    file_name: str
    file_path: str
    upload_date: datetime = Field(default_factory=datetime.utcnow)
    verified: bool = False
    verification_date: Optional[datetime] = None
    extracted_data: Dict[str, Any] = Field(default_factory=dict)
    verification_notes: str = ""


class LoanDetails(BaseModel):
    """Loan request details"""
    loan_type: LoanType
    requested_amount: float
    loan_term_months: int
    purpose: str
    down_payment: float = 0.0
    collateral_value: Optional[float] = None
    collateral_description: Optional[str] = None
    property_address: Optional[Address] = None  # For mortgages/auto
    interest_rate: Optional[float] = None
    monthly_payment: Optional[float] = None


class CreditAnalysis(BaseModel):
    """Credit analysis results"""
    credit_score: int
    credit_history_length_years: float
    payment_history_score: float = Field(ge=0, le=100)
    credit_utilization: float = Field(ge=0, le=100)
    recent_inquiries: int
    derogatory_marks: int
    accounts_in_good_standing: int
    total_accounts: int
    debt_to_income_ratio: float
    analysis_summary: str = ""
    risk_factors: List[str] = Field(default_factory=list)
    positive_factors: List[str] = Field(default_factory=list)
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)
    analyzed_by: str = "credit_analysis_agent"


class IncomeVerification(BaseModel):
    """Income verification results"""
    stated_monthly_income: float
    verified_monthly_income: float
    verification_method: str  # paystub, bank_statement, tax_return, employer_contact
    employment_verified: bool
    income_stability_score: float = Field(ge=0, le=100)
    verification_documents: List[str] = Field(default_factory=list)
    discrepancies: List[str] = Field(default_factory=list)
    verification_notes: str = ""
    verified_at: datetime = Field(default_factory=datetime.utcnow)
    verified_by: str = "income_verification_agent"


class RiskAssessment(BaseModel):
    """Risk assessment results"""
    overall_risk_level: RiskLevel
    risk_score: float = Field(ge=0, le=100)
    probability_of_default: float = Field(ge=0, le=100)
    loan_to_value_ratio: Optional[float] = None
    debt_service_coverage_ratio: Optional[float] = None
    risk_factors: List[Dict[str, Any]] = Field(default_factory=list)
    mitigating_factors: List[str] = Field(default_factory=list)
    recommendation: str  # approve, approve_with_conditions, deny
    recommended_interest_rate: Optional[float] = None
    recommended_loan_amount: Optional[float] = None
    conditions: List[str] = Field(default_factory=list)
    assessed_at: datetime = Field(default_factory=datetime.utcnow)
    assessed_by: str = "risk_assessment_agent"


class ComplianceCheck(BaseModel):
    """Regulatory compliance verification"""
    compliant: bool
    regulations_checked: List[str] = Field(default_factory=list)
    violations: List[Dict[str, str]] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    fair_lending_check: bool = True
    anti_discrimination_check: bool = True
    ability_to_repay_verified: bool = False
    required_disclosures: List[str] = Field(default_factory=list)
    compliance_notes: str = ""
    checked_at: datetime = Field(default_factory=datetime.utcnow)
    checked_by: str = "compliance_agent"


class UnderwritingDecision(BaseModel):
    """Final underwriting decision"""
    decision: str  # approved, conditionally_approved, denied
    approved_amount: Optional[float] = None
    approved_term_months: Optional[int] = None
    interest_rate: Optional[float] = None
    monthly_payment: Optional[float] = None
    conditions: List[str] = Field(default_factory=list)
    denial_reasons: List[str] = Field(default_factory=list)
    decision_explanation: str = ""
    confidence_score: float = Field(ge=0, le=100)
    decided_at: datetime = Field(default_factory=datetime.utcnow)
    decided_by: str = "coordinator_agent"
    human_review_required: bool = False
    human_reviewer: Optional[str] = None
    human_review_notes: Optional[str] = None


# ============================================================================
# Main Loan Application Model
# ============================================================================

class LoanApplication(BaseModel):
    """Complete loan application"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    application_id: str = Field(default_factory=lambda: f"LOAN-{datetime.utcnow().strftime('%Y%m%d')}-{str(ObjectId())[:8]}")

    # Borrower Information
    borrower_first_name: str
    borrower_last_name: str
    borrower_email: str
    borrower_phone: str
    date_of_birth: datetime
    ssn_last_4: str  # Last 4 digits only for security
    current_address: Address

    # Employment & Financial
    employment: Employment
    financial_info: FinancialInformation

    # Loan Details
    loan_details: LoanDetails

    # Documents
    uploaded_documents: List[Document] = Field(default_factory=list)

    # Analysis Results (populated by agents)
    credit_analysis: Optional[CreditAnalysis] = None
    income_verification: Optional[IncomeVerification] = None
    risk_assessment: Optional[RiskAssessment] = None
    compliance_check: Optional[ComplianceCheck] = None

    # Final Decision
    underwriting_decision: Optional[UnderwritingDecision] = None

    # Status & Tracking
    status: LoanStatus = LoanStatus.SUBMITTED
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    processing_time_minutes: Optional[float] = None

    # Agent Activity Log
    agent_activity: List[Dict[str, Any]] = Field(default_factory=list)

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


# ============================================================================
# Borrower Model (for repeat customers)
# ============================================================================

class Borrower(BaseModel):
    """Borrower profile for repeat customers"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    borrower_id: str = Field(default_factory=lambda: f"BRW-{str(ObjectId())[:12]}")

    first_name: str
    last_name: str
    email: str
    phone: str
    date_of_birth: datetime
    ssn_last_4: str

    # Application History
    total_applications: int = 0
    approved_applications: int = 0
    denied_applications: int = 0
    active_loans: List[str] = Field(default_factory=list)
    payment_history: List[Dict[str, Any]] = Field(default_factory=list)

    # Risk Profile
    current_credit_score: Optional[int] = None
    risk_level: Optional[RiskLevel] = None

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_application_date: Optional[datetime] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


# ============================================================================
# Performance Metrics
# ============================================================================

class UnderwritingMetrics(BaseModel):
    """System performance metrics"""
    date: datetime = Field(default_factory=datetime.utcnow)

    # Volume Metrics
    total_applications: int = 0
    approved_applications: int = 0
    denied_applications: int = 0
    pending_applications: int = 0

    # Performance Metrics
    average_processing_time_minutes: float = 0.0
    approval_rate: float = 0.0
    denial_rate: float = 0.0

    # Quality Metrics
    ai_accuracy: float = 0.0  # % of AI decisions confirmed by human review
    human_override_rate: float = 0.0

    # Risk Metrics
    average_credit_score: float = 0.0
    average_dti_ratio: float = 0.0
    high_risk_applications: int = 0

    # Financial Metrics
    total_loan_amount_approved: float = 0.0
    average_loan_amount: float = 0.0
    weighted_average_interest_rate: float = 0.0

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
