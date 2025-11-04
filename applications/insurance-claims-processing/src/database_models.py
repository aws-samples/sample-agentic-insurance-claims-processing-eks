"""
Database Models for Insurance Claims Processing
MongoDB data models and database operations
"""

from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field, field_validator
from bson import ObjectId
import os
import logging

logger = logging.getLogger(__name__)

# Pydantic models for data validation
class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):
        from pydantic_core import core_schema
        return core_schema.no_info_plain_validator_function(cls.validate)

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema, handler):
        field_schema.update(type="string")
        return field_schema

class ClaimDocument(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    claim_id: str = Field(..., description="Unique claim identifier")
    policy_number: str = Field(..., description="Policy number")
    customer_name: str = Field(..., description="Customer name")
    customer_email: Optional[str] = Field(None, description="Customer email")
    claim_type: str = Field(..., description="Type of claim (collision, comprehensive, etc.)")
    incident_date: datetime = Field(..., description="Date of incident")
    reported_date: datetime = Field(default_factory=datetime.utcnow, description="Date claim was reported")
    claim_amount: float = Field(..., description="Claimed amount")
    description: str = Field(..., description="Claim description")
    location: Optional[Union[Dict[str, Any], str]] = Field(None, description="Incident location")

    @field_validator('location')
    @classmethod
    def convert_location_to_dict(cls, v):
        """Convert location string to dict format"""
        if isinstance(v, str):
            return {"city": v, "type": "string"}
        return v

    # Processing status
    status: str = Field(default="submitted", description="Claim status")
    current_stage: str = Field(default="initial_review", description="Current processing stage")

    # AI Analysis Results
    ai_recommendation: Optional[Dict[str, Any]] = Field(None, description="AI analysis results")
    fraud_analysis: Optional[Dict[str, Any]] = Field(None, description="Fraud analysis results")
    policy_analysis: Optional[Dict[str, Any]] = Field(None, description="Policy analysis results")

    # Human Workflow
    assigned_adjuster: Optional[str] = Field(None, description="Assigned claims adjuster")
    human_decision: Optional[Dict[str, Any]] = Field(None, description="Final human decision")

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}

class CustomerDocument(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    customer_id: str = Field(..., description="Unique customer identifier")
    name: str = Field(..., description="Customer name")
    email: str = Field(..., description="Customer email")
    phone: Optional[str] = Field(None, description="Customer phone")
    address: Optional[Dict[str, str]] = Field(None, description="Customer address")

    # Policy information
    policies: List[str] = Field(default_factory=list, description="List of policy numbers")

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}

class TaskDocument(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    task_id: str = Field(..., description="Unique task identifier")
    claim_id: str = Field(..., description="Associated claim ID")
    task_type: str = Field(..., description="Type of task")
    assigned_to: str = Field(..., description="Assigned user/role")
    priority: str = Field(default="medium", description="Task priority")
    status: str = Field(default="pending", description="Task status")

    # Task details
    title: str = Field(..., description="Task title")
    description: str = Field(..., description="Task description")
    due_date: Optional[datetime] = Field(None, description="Task due date")

    # Decision information
    decision: Optional[Dict[str, Any]] = Field(None, description="Task decision")

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(None, description="Task completion time")

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}

class DatabaseManager:
    """MongoDB database manager for insurance claims processing"""

    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.database = None

    async def connect(self):
        """Connect to MongoDB"""
        try:
            # MongoDB connection string
            mongodb_url = os.getenv(
                "MONGODB_URL",
                "mongodb://admin:<YOUR_MONGODB_PASSWORD>@mongodb-service.database.svc.cluster.local:27017/claims_db?authSource=admin"
            )

            self.client = AsyncIOMotorClient(mongodb_url)
            self.database = self.client.claims_db

            # Test connection
            await self.client.admin.command('ping')
            logger.info("Successfully connected to MongoDB")

            # Create indexes
            await self._create_indexes()

        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    async def disconnect(self):
        """Disconnect from MongoDB"""
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")

    async def _create_indexes(self):
        """Create database indexes for performance"""
        try:
            # Claims collection indexes
            await self.database.claims.create_index("claim_id", unique=True)
            await self.database.claims.create_index("policy_number")
            await self.database.claims.create_index("status")
            await self.database.claims.create_index("created_at")

            # Customers collection indexes
            await self.database.customers.create_index("customer_id", unique=True)
            await self.database.customers.create_index("email", unique=True)

            # Tasks collection indexes
            await self.database.tasks.create_index("task_id", unique=True)
            await self.database.tasks.create_index("claim_id")
            await self.database.tasks.create_index("assigned_to")
            await self.database.tasks.create_index("status")

            logger.info("Database indexes created successfully")

        except Exception as e:
            logger.warning(f"Failed to create some indexes: {e}")

    # Claims operations
    async def create_claim(self, claim_data: Dict[str, Any]) -> str:
        """Create a new claim"""
        claim = ClaimDocument(**claim_data)
        result = await self.database.claims.insert_one(claim.dict(by_alias=True))
        return str(result.inserted_id)

    async def get_claim(self, claim_id: str) -> Optional[Dict[str, Any]]:
        """Get claim by ID"""
        claim = await self.database.claims.find_one({"claim_id": claim_id})
        if claim:
            claim["_id"] = str(claim["_id"])
        return claim

    async def update_claim(self, claim_id: str, update_data: Dict[str, Any]) -> bool:
        """Update claim"""
        update_data["updated_at"] = datetime.utcnow()
        result = await self.database.claims.update_one(
            {"claim_id": claim_id},
            {"$set": update_data}
        )
        return result.modified_count > 0

    async def list_claims(self, skip: int = 0, limit: int = 50, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """List claims with pagination"""
        query = {}
        if status:
            query["status"] = status

        cursor = self.database.claims.find(query).skip(skip).limit(limit).sort("created_at", -1)
        claims = []
        async for claim in cursor:
            claim["_id"] = str(claim["_id"])
            claims.append(claim)
        return claims

    async def count_claims(self, status: Optional[str] = None) -> int:
        """Count total claims"""
        query = {}
        if status:
            query["status"] = status
        return await self.database.claims.count_documents(query)

    # Customer operations
    async def create_customer(self, customer_data: Dict[str, Any]) -> str:
        """Create a new customer"""
        customer = CustomerDocument(**customer_data)
        result = await self.database.customers.insert_one(customer.dict(by_alias=True))
        return str(result.inserted_id)

    async def get_customer(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """Get customer by ID"""
        customer = await self.database.customers.find_one({"customer_id": customer_id})
        if customer:
            customer["_id"] = str(customer["_id"])
        return customer

    # Task operations
    async def create_task(self, task_data: Dict[str, Any]) -> str:
        """Create a new task"""
        task = TaskDocument(**task_data)
        result = await self.database.tasks.insert_one(task.dict(by_alias=True))
        return str(result.inserted_id)

    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task by ID"""
        task = await self.database.tasks.find_one({"task_id": task_id})
        if task:
            task["_id"] = str(task["_id"])
        return task

    async def update_task(self, task_id: str, update_data: Dict[str, Any]) -> bool:
        """Update task"""
        update_data["updated_at"] = datetime.utcnow()
        if update_data.get("status") == "completed":
            update_data["completed_at"] = datetime.utcnow()

        result = await self.database.tasks.update_one(
            {"task_id": task_id},
            {"$set": update_data}
        )
        return result.modified_count > 0

    async def get_tasks_for_user(self, assigned_to: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get tasks assigned to a user"""
        query = {"assigned_to": assigned_to}
        if status:
            query["status"] = status

        cursor = self.database.tasks.find(query).sort("created_at", -1)
        tasks = []
        async for task in cursor:
            task["_id"] = str(task["_id"])
            tasks.append(task)
        return tasks

# Global database manager instance
db_manager = DatabaseManager()