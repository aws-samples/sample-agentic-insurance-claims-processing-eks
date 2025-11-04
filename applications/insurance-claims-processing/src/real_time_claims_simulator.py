"""
Real-Time Insurance Claims Simulator for Live Demos
Generates realistic insurance claim streams with fraud patterns for demonstration
"""

import asyncio
import json
import logging
import random
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum

import redis.asyncio as redis
import aiohttp
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks
from pydantic import BaseModel
import numpy as np
from faker import Faker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Use cryptographically secure random for security-sensitive operations
secure_random = secrets.SystemRandom()

class ClaimType(Enum):
    AUTO = "auto"
    PROPERTY = "property"
    HEALTH = "health"
    LIABILITY = "liability"
    WORKERS_COMP = "workers_comp"

class FraudType(Enum):
    STAGED_ACCIDENT = "staged_accident"
    INFLATED_CLAIM = "inflated_claim"
    FALSE_INJURY = "false_injury"
    EXAGGERATED_DAMAGES = "exaggerated_damages"
    IDENTITY_FRAUD = "identity_fraud"
    PROVIDER_FRAUD = "provider_fraud"

@dataclass
class Customer:
    customer_id: str
    name: str
    age: int
    location: str
    policy_start_date: datetime
    claim_history_count: int
    risk_profile: str
    is_high_risk: bool = False

@dataclass
class Claim:
    claim_id: str
    policy_number: str
    customer_id: str
    customer_name: str  # Added for database compatibility
    claim_type: ClaimType
    claim_amount: float
    incident_date: datetime
    reported_date: datetime
    description: str
    location: str

    # Fraud indicators
    fraud_indicators: List[str]
    fraud_score: float
    is_suspicious: bool

    # Processing metadata
    priority: str
    estimated_processing_time: float
    requires_investigation: bool

    # Demo metadata
    timestamp: str
    demo_scenario: Optional[str] = None

class InsuranceClaimsGenerator:
    """Generates realistic insurance claims with embedded fraud patterns"""
    
    def __init__(self):
        self.fake = Faker()
        self.customers = self._generate_customer_base()
        self.claim_counter = 0
        
        # Fraud pattern templates
        self.fraud_patterns = {
            "staged_accident": {
                "indicators": ["multiple_claims_same_location", "witnesses_related", "excessive_medical_bills"],
                "description_templates": [
                    "Multi-vehicle accident on Highway {highway} involving {vehicles} vehicles",
                    "Intersection collision at {location} with {injuries} claimed injuries",
                    "Rear-end collision in parking lot with immediate attorney involvement"
                ],
                "amount_range": (15000, 75000),
                "fraud_score_range": (0.7, 0.9)
            },
            "inflated_claim": {
                "indicators": ["amount_inconsistent_with_damage", "delayed_reporting", "multiple_estimates"],
                "description_templates": [
                    "Storm damage to roof requiring complete replacement",
                    "Water damage from burst pipe affecting entire basement",
                    "Fire damage to kitchen requiring full renovation"
                ],
                "amount_range": (25000, 150000),
                "fraud_score_range": (0.6, 0.8)
            },
            "false_injury": {
                "indicators": ["soft_tissue_injury", "no_medical_history", "attorney_involvement"],
                "description_templates": [
                    "Slip and fall in grocery store with back injury",
                    "Minor fender bender with neck pain and headaches",
                    "Workplace injury with chronic pain syndrome"
                ],
                "amount_range": (8000, 45000),
                "fraud_score_range": (0.65, 0.85)
            }
        }
    
    def _generate_customer_base(self) -> List[Customer]:
        """Generate diverse customer base"""
        customers = []
        
        # Normal customers (80%)
        for i in range(400):
            customers.append(Customer(
                customer_id=f"CUST_{i:06d}",
                name=self.fake.name(),
                age=secure_random.randint(25, 70),
                location=self.fake.city(),
                policy_start_date=self.fake.date_between(start_date='-5y', end_date='today'),
                claim_history_count=secure_random.randint(0, 3),
                risk_profile=secure_random.choice(["low", "medium"]),
                is_high_risk=False
            ))
        
        # High-risk customers (20%)
        for i in range(100):
            customers.append(Customer(
                customer_id=f"HRISK_{i:03d}",
                name=self.fake.name(),
                age=secure_random.randint(20, 60),
                location=self.fake.city(),
                policy_start_date=self.fake.date_between(start_date='-2y', end_date='today'),
                claim_history_count=secure_random.randint(3, 12),
                risk_profile=secure_random.choice(["high", "critical"]),
                is_high_risk=True
            ))
        
        return customers
    
    def generate_normal_claim(self) -> Claim:
        """Generate a normal, legitimate insurance claim"""
        customer = secure_random.choice([c for c in self.customers if not c.is_high_risk])
        claim_type = secure_random.choice(list(ClaimType))
        
        # Generate claim amount based on type
        amount_ranges = {
            ClaimType.AUTO: (2000, 25000),
            ClaimType.PROPERTY: (5000, 50000),
            ClaimType.HEALTH: (1000, 15000),
            ClaimType.LIABILITY: (3000, 30000),
            ClaimType.WORKERS_COMP: (5000, 40000)
        }
        
        amount_range = amount_ranges[claim_type]
        claim_amount = secure_random.uniform(*amount_range)
        
        # Generate description
        descriptions = {
            ClaimType.AUTO: [
                "Minor collision in parking lot with scratches to bumper",
                "Hail damage to vehicle during storm",
                "Tree branch fell on car during windstorm"
            ],
            ClaimType.PROPERTY: [
                "Kitchen fire caused by faulty appliance",
                "Basement flooding from heavy rains",
                "Wind damage to roof shingles"
            ],
            ClaimType.HEALTH: [
                "Routine medical procedure",
                "Emergency room visit for food poisoning",
                "Physical therapy for sports injury"
            ]
        }
        
        description = secure_random.choice(descriptions.get(claim_type, ["Standard claim"]))

        incident_date = self.fake.date_between(start_date='-30d', end_date='today')
        reported_date = incident_date + timedelta(days=secure_random.randint(1, 7))
        
        self.claim_counter += 1
        
        return Claim(
            claim_id=f"CLM_{self.claim_counter:08d}",
            policy_number=f"POL_{customer.customer_id}",
            customer_id=customer.customer_id,
            customer_name=customer.name,  # Add customer name
            claim_type=claim_type,
            claim_amount=claim_amount,
            incident_date=incident_date,
            reported_date=reported_date,
            description=description,
            location=customer.location,
            fraud_indicators=[],
            fraud_score=secure_random.uniform(0.0, 0.3),
            is_suspicious=False,
            priority="normal",
            estimated_processing_time=secure_random.uniform(2.0, 8.0),
            requires_investigation=False,
            timestamp=datetime.utcnow().isoformat()
        )
    
    def generate_suspicious_claim(self, fraud_type: str = None) -> Claim:
        """Generate a suspicious claim with fraud indicators"""
        customer = secure_random.choice([c for c in self.customers if c.is_high_risk])

        if not fraud_type:
            fraud_type = secure_random.choice(list(self.fraud_patterns.keys()))
        
        pattern = self.fraud_patterns[fraud_type]
        
        # Select claim type based on fraud pattern
        claim_type_mapping = {
            "staged_accident": ClaimType.AUTO,
            "inflated_claim": secure_random.choice([ClaimType.PROPERTY, ClaimType.AUTO]),
            "false_injury": secure_random.choice([ClaimType.LIABILITY, ClaimType.WORKERS_COMP])
        }
        
        claim_type = claim_type_mapping.get(fraud_type, ClaimType.AUTO)
        
        # Generate fraudulent claim amount
        amount_range = pattern["amount_range"]
        claim_amount = secure_random.uniform(*amount_range)
        
        # Generate description
        description_template = secure_random.choice(pattern["description_templates"])
        description = description_template.format(
            highway=secure_random.randint(1, 101),
            vehicles=secure_random.randint(2, 4),
            location=self.fake.street_name(),
            injuries=secure_random.randint(2, 5)
        )
        
        # Generate fraud score
        fraud_score_range = pattern["fraud_score_range"]
        fraud_score = secure_random.uniform(*fraud_score_range)
        
        # Suspicious timing patterns
        incident_date = self.fake.date_between(start_date='-60d', end_date='-1d')
        # Delayed reporting is suspicious
        reported_date = incident_date + timedelta(days=secure_random.randint(14, 45))
        
        self.claim_counter += 1
        
        return Claim(
            claim_id=f"SUSP_{self.claim_counter:08d}",
            policy_number=f"POL_{customer.customer_id}",
            customer_id=customer.customer_id,
            customer_name=customer.name,  # Add customer name
            claim_type=claim_type,
            claim_amount=claim_amount,
            incident_date=incident_date,
            reported_date=reported_date,
            description=description,
            location=customer.location,
            fraud_indicators=pattern["indicators"],
            fraud_score=fraud_score,
            is_suspicious=True,
            priority="high",
            estimated_processing_time=secure_random.uniform(15.0, 45.0),
            requires_investigation=True,
            timestamp=datetime.utcnow().isoformat(),
            demo_scenario=fraud_type
        )
    
    def generate_scenario_claims(self, scenario_type: str) -> List[Claim]:
        """Generate specific fraud scenario claims"""
        claims = []
        
        if scenario_type == "staged_accident_ring":
            # Generate multiple related staged accidents
            base_location = self.fake.city()
            for i in range(3):
                claim = self.generate_suspicious_claim("staged_accident")
                claim.location = base_location
                claim.description = f"Staged accident #{i+1} in {base_location} - part of organized ring"
                claim.fraud_indicators.append("organized_fraud_ring")
                claims.append(claim)
        
        elif scenario_type == "serial_fraudster":
            # Single customer with multiple suspicious claims
            fraudster = secure_random.choice([c for c in self.customers if c.is_high_risk])
            for i in range(2):
                claim = self.generate_suspicious_claim()
                claim.customer_id = fraudster.customer_id
                claim.fraud_indicators.append("serial_claimant")
                claims.append(claim)
        
        elif scenario_type == "inflated_storm_claims":
            # Multiple inflated claims from same storm event
            storm_date = datetime.now() - timedelta(days=secure_random.randint(5, 15))
            for i in range(4):
                claim = self.generate_suspicious_claim("inflated_claim")
                claim.incident_date = storm_date
                claim.description = f"Storm damage claim #{i+1} - Hurricane Miranda"
                claim.fraud_indicators.append("coordinated_inflation")
                claims.append(claim)
        
        return claims

class RealTimeClaimsSimulator:
    """Real-time insurance claims simulator"""
    
    def __init__(self, redis_url: str = "redis://redis-service:6379"):
        self.claims_generator = InsuranceClaimsGenerator()
        self.redis_url = redis_url
        self.redis_client = None
        self.active_connections: List[WebSocket] = []
        self.running = False

        # Stream configuration
        self.claims_per_minute = 20  # More realistic pace for insurance
        self.fraud_rate = 0.25  # 25% fraud rate for demo visibility

        # Demo cap: stop generating after 25,000 claims
        self.max_claims_for_demo = 25000
        
    async def initialize(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.from_url(self.redis_url)
            await self.redis_client.ping()
            logger.info("Connected to Redis for claims streaming")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")
    
    async def start_streaming(self):
        """Start the claims stream"""
        self.running = True
        logger.info("Starting real-time insurance claims stream")

        while self.running:
            try:
                # Check if we've hit the demo cap
                if self.claims_generator.claim_counter >= self.max_claims_for_demo:
                    logger.info(f"Demo cap reached: {self.max_claims_for_demo} claims generated. Pausing generation.")
                    await asyncio.sleep(5)  # Wait before checking again
                    continue

                # Generate claim based on probability
                if secure_random.random() < self.fraud_rate:
                    claim = self.claims_generator.generate_suspicious_claim()
                else:
                    claim = self.claims_generator.generate_normal_claim()
                
                # Convert to dict
                claim_dict = asdict(claim)
                claim_dict["claim_type"] = claim.claim_type.value
                claim_dict["incident_date"] = claim.incident_date.isoformat()
                claim_dict["reported_date"] = claim.reported_date.isoformat()
                
                # Send to Redis stream
                if self.redis_client:
                    # Convert all values to strings for Redis
                    redis_claim = {}
                    for key, value in claim_dict.items():
                        if isinstance(value, list):
                            redis_claim[key] = json.dumps(value)
                        else:
                            redis_claim[key] = str(value)

                    await self.redis_client.xadd(
                        "insurance_claims_stream",
                        redis_claim
                    )
                
                # Send to WebSocket connections
                await self._broadcast_claim(claim_dict)
                
                # Send to insurance processing system
                await self._send_to_insurance_system(claim_dict)
                
                # Control streaming rate
                await asyncio.sleep(60.0 / self.claims_per_minute)
                
            except Exception as e:
                logger.error(f"Claims streaming error: {e}")
                await asyncio.sleep(1)
    
    async def _broadcast_claim(self, claim: Dict[str, Any]):
        """Broadcast claim to WebSocket connections"""
        if self.active_connections:
            message = json.dumps({
                "type": "new_claim",
                "data": claim,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Remove closed connections
            dead_connections = []
            for connection in self.active_connections:
                try:
                    await connection.send_text(message)
                except:
                    dead_connections.append(connection)
            
            for dead_conn in dead_connections:
                self.active_connections.remove(dead_conn)
    
    async def _send_to_insurance_system(self, claim: Dict[str, Any]):
        """Send claim to insurance processing system"""
        try:
            async with aiohttp.ClientSession() as session:
                # Send to Insurance Coordinator
                async with session.post(
                    "http://coordinator-service:8000/coordinate",
                    json=claim,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get("investigation_required"):
                            logger.info(f"Claim {claim['claim_id']} flagged for investigation")
                        
                        # Send processing result to WebSocket
                        await self._broadcast_processing_result(claim['claim_id'], result)
                    
        except Exception as e:
            logger.debug(f"Insurance system communication error: {e}")
    
    async def _broadcast_processing_result(self, claim_id: str, result: Dict[str, Any]):
        """Broadcast processing result to WebSocket connections"""
        if self.active_connections:
            message = json.dumps({
                "type": "claim_processed",
                "claim_id": claim_id,
                "result": result,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            for connection in self.active_connections:
                try:
                    await connection.send_text(message)
                except:
                    pass
    
    async def generate_scenario(self, scenario_type: str) -> List[Dict[str, Any]]:
        """Generate specific fraud scenarios for demonstration"""
        claims = self.claims_generator.generate_scenario_claims(scenario_type)
        
        processed_claims = []
        for claim in claims:
            claim_dict = asdict(claim)
            claim_dict["claim_type"] = claim.claim_type.value
            claim_dict["incident_date"] = claim.incident_date.isoformat()
            claim_dict["reported_date"] = claim.reported_date.isoformat()
            
            # Send through the system
            await self._send_to_insurance_system(claim_dict)
            await self._broadcast_claim(claim_dict)
            
            processed_claims.append(claim_dict)
            
            # Small delay between related claims
            await asyncio.sleep(2)
        
        return processed_claims
    
    async def add_websocket_connection(self, websocket: WebSocket):
        """Add WebSocket connection"""
        self.active_connections.append(websocket)
        logger.info(f"Added WebSocket connection. Total: {len(self.active_connections)}")
    
    async def remove_websocket_connection(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"Removed WebSocket connection. Total: {len(self.active_connections)}")
    
    async def get_stream_statistics(self) -> Dict[str, Any]:
        """Get streaming statistics"""
        if not self.redis_client:
            return {"error": "Redis not connected"}

        try:
            # Get stream info
            stream_info = await self.redis_client.xinfo_stream("insurance_claims_stream")

            claims_count = self.claims_generator.claim_counter
            cap_reached = claims_count >= self.max_claims_for_demo

            return {
                "stream_length": stream_info["length"],
                "active_websocket_connections": len(self.active_connections),
                "claims_per_minute": self.claims_per_minute,
                "fraud_rate": self.fraud_rate,
                "claims_generated": claims_count,
                "max_claims_demo_cap": self.max_claims_for_demo,
                "cap_reached": cap_reached,
                "status": "paused - demo cap reached" if cap_reached else "active",
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Statistics error: {e}")
            return {"error": str(e)}

# FastAPI Application
app = FastAPI(
    title="Real-Time Insurance Claims Simulator",
    description="Live insurance claims generator with fraud patterns for demonstrations",
    version="1.0.0"
)

# Global simulator instance
simulator: Optional[RealTimeClaimsSimulator] = None

@app.on_event("startup")
async def startup_event():
    global simulator
    simulator = RealTimeClaimsSimulator()
    await simulator.initialize()
    
    # Start streaming in background
    asyncio.create_task(simulator.start_streaming())
    logger.info("Real-Time Insurance Claims Simulator started")

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "insurance-claims-simulator",
        "streaming": simulator.running if simulator else False,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/statistics")
async def get_statistics():
    if not simulator:
        return {"error": "Simulator not initialized"}
    return await simulator.get_stream_statistics()

@app.post("/scenario/{scenario_type}")
async def generate_scenario(scenario_type: str):
    """Generate specific fraud scenarios"""
    if not simulator:
        return {"error": "Simulator not initialized"}
    
    claims = await simulator.generate_scenario(scenario_type)
    
    return {
        "scenario": scenario_type,
        "claims_generated": len(claims),
        "claims": claims
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    if simulator:
        await simulator.add_websocket_connection(websocket)
    
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        if simulator:
            await simulator.remove_websocket_connection(websocket)

@app.get("/scenarios")
async def get_available_scenarios():
    return {
        "available_scenarios": [
            {
                "name": "staged_accident_ring",
                "description": "Multiple coordinated staged accidents in same area"
            },
            {
                "name": "serial_fraudster", 
                "description": "Single customer with multiple suspicious claims"
            },
            {
                "name": "inflated_storm_claims",
                "description": "Coordinated inflation of storm damage claims"
            }
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8091)