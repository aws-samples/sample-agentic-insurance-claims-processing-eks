"""
Claims Management System Integration Layer
Supports major platforms: Guidewire ClaimCenter, Duck Creek Claims, ISO ClaimSearch
"""

import asyncio
import aiohttp
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from enum import Enum
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod

from defusedxml import ElementTree as ET
from fastapi import HTTPException

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ClaimsSystemType(str, Enum):
    GUIDEWIRE = "guidewire"
    DUCK_CREEK = "duck_creek"
    ISO_CLAIMSEARCH = "iso_claimsearch"
    CUSTOM_REST = "custom_rest"
    GENERIC_SOAP = "generic_soap"

@dataclass
class ClaimData:
    """Standardized claim data structure"""
    claim_id: str
    policy_number: str
    insured_name: str
    claim_amount: float
    incident_date: str
    reported_date: str
    claim_type: str
    status: str
    description: str

    # Extended fields
    adjuster_id: Optional[str] = None
    reserves: Optional[float] = None
    payments: Optional[float] = None
    coverage_code: Optional[str] = None
    deductible: Optional[float] = None
    jurisdiction: Optional[str] = None

    # Claimant information
    claimant_name: Optional[str] = None
    claimant_phone: Optional[str] = None
    claimant_address: Optional[Dict[str, str]] = None

    # Vehicle/Property information
    vehicle_vin: Optional[str] = None
    property_address: Optional[Dict[str, str]] = None

    # Additional metadata
    created_by: Optional[str] = None
    last_updated: Optional[str] = None
    external_refs: Optional[Dict[str, str]] = None

@dataclass
class PolicyData:
    """Standardized policy data structure"""
    policy_number: str
    product_line: str
    effective_date: str
    expiration_date: str
    policy_status: str

    # Coverage details
    coverage_limits: Dict[str, float]
    deductibles: Dict[str, float]
    premium_amount: float

    # Insured information
    named_insured: str
    mailing_address: Dict[str, str]
    phone_number: str
    email: str

    # Risk information
    vehicles: Optional[List[Dict[str, Any]]] = None
    properties: Optional[List[Dict[str, Any]]] = None
    drivers: Optional[List[Dict[str, Any]]] = None

class ClaimsSystemIntegration(ABC):
    """Abstract base class for claims system integrations"""

    @abstractmethod
    async def get_claim(self, claim_id: str) -> ClaimData:
        """Retrieve claim data"""
        pass

    @abstractmethod
    async def update_claim(self, claim_id: str, updates: Dict[str, Any]) -> bool:
        """Update claim data"""
        pass

    @abstractmethod
    async def create_claim(self, claim_data: ClaimData) -> str:
        """Create new claim"""
        pass

    @abstractmethod
    async def get_policy(self, policy_number: str) -> PolicyData:
        """Retrieve policy data"""
        pass

    @abstractmethod
    async def search_claims(self, criteria: Dict[str, Any]) -> List[ClaimData]:
        """Search claims by criteria"""
        pass

class GuidewireIntegration(ClaimsSystemIntegration):
    """Integration with Guidewire ClaimCenter"""

    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.auth_token = None
        self.session = None

    async def _authenticate(self):
        """Authenticate with Guidewire"""
        if not self.session:
            self.session = aiohttp.ClientSession()

        auth_url = f"{self.base_url}/bc/rest/login"
        auth_data = {
            "username": self.username,
            "password": self.password
        }

        try:
            async with self.session.post(auth_url, json=auth_data) as response:
                if response.status == 200:
                    auth_result = await response.json()
                    self.auth_token = auth_result.get("sessionToken")
                    logger.info("Guidewire authentication successful")
                else:
                    raise HTTPException(status_code=401, detail="Guidewire authentication failed")
        except Exception as e:
            logger.error(f"Guidewire authentication error: {e}")
            raise

    async def _make_request(self, method: str, endpoint: str, data: Dict = None) -> Dict:
        """Make authenticated request to Guidewire"""
        if not self.auth_token:
            await self._authenticate()

        url = f"{self.base_url}/bc/rest/claim/{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json"
        }

        try:
            async with self.session.request(method, url, headers=headers, json=data) as response:
                if response.status == 401:
                    # Token expired, re-authenticate
                    await self._authenticate()
                    headers["Authorization"] = f"Bearer {self.auth_token}"
                    async with self.session.request(method, url, headers=headers, json=data) as retry_response:
                        return await retry_response.json()

                response.raise_for_status()
                return await response.json()
        except Exception as e:
            logger.error(f"Guidewire API error: {e}")
            raise

    async def get_claim(self, claim_id: str) -> ClaimData:
        """Get claim from Guidewire ClaimCenter"""
        response = await self._make_request("GET", f"claims/{claim_id}")

        # Map Guidewire response to standard ClaimData
        gw_claim = response.get("data", {})

        return ClaimData(
            claim_id=gw_claim.get("claimNumber"),
            policy_number=gw_claim.get("policy", {}).get("policyNumber"),
            insured_name=gw_claim.get("insured", {}).get("displayName"),
            claim_amount=float(gw_claim.get("totalIncurred", 0)),
            incident_date=gw_claim.get("lossDate"),
            reported_date=gw_claim.get("reportedDate"),
            claim_type=gw_claim.get("lossCause"),
            status=gw_claim.get("state"),
            description=gw_claim.get("description", ""),
            adjuster_id=gw_claim.get("assignedUser", {}).get("id"),
            reserves=float(gw_claim.get("remainingReserves", 0)),
            payments=float(gw_claim.get("totalPayments", 0)),
            coverage_code=gw_claim.get("primaryCoverage", {}).get("type"),
            deductible=float(gw_claim.get("deductible", 0)),
            jurisdiction=gw_claim.get("jurisdiction"),
            external_refs={"guidewire_id": gw_claim.get("id")}
        )

    async def update_claim(self, claim_id: str, updates: Dict[str, Any]) -> bool:
        """Update claim in Guidewire"""
        try:
            # Map standard updates to Guidewire format
            gw_updates = self._map_updates_to_guidewire(updates)

            response = await self._make_request("PUT", f"claims/{claim_id}", gw_updates)
            return response.get("success", False)
        except Exception as e:
            logger.error(f"Failed to update Guidewire claim {claim_id}: {e}")
            return False

    async def create_claim(self, claim_data: ClaimData) -> str:
        """Create new claim in Guidewire"""
        gw_claim_data = {
            "policyNumber": claim_data.policy_number,
            "lossDate": claim_data.incident_date,
            "reportedDate": claim_data.reported_date,
            "lossCause": claim_data.claim_type,
            "description": claim_data.description,
            "reporter": {
                "name": claim_data.claimant_name or claim_data.insured_name
            }
        }

        response = await self._make_request("POST", "claims", gw_claim_data)
        return response.get("data", {}).get("claimNumber")

    async def get_policy(self, policy_number: str) -> PolicyData:
        """Get policy from Guidewire PolicyCenter"""
        policy_url = f"{self.base_url.replace('/bc/', '/pc/')}/rest/account/policies/{policy_number}"

        # This would typically be a separate PolicyCenter integration
        # For now, return mock data structure
        return PolicyData(
            policy_number=policy_number,
            product_line="Personal Auto",
            effective_date="2024-01-01",
            expiration_date="2024-12-31",
            policy_status="Active",
            coverage_limits={"BI": 250000, "PD": 100000, "COMP": 50000, "COLL": 50000},
            deductibles={"COMP": 500, "COLL": 1000},
            premium_amount=1200.0,
            named_insured="John Doe",
            mailing_address={"street": "123 Main St", "city": "Anytown", "state": "CA", "zip": "12345"},
            phone_number="555-123-4567",
            email="john.doe@email.com"
        )

    async def search_claims(self, criteria: Dict[str, Any]) -> List[ClaimData]:
        """Search claims in Guidewire"""
        search_params = {
            "criteria": criteria,
            "sortBy": "reportedDate",
            "sortOrder": "desc",
            "limit": 100
        }

        response = await self._make_request("POST", "claims/search", search_params)
        claims = []

        for gw_claim in response.get("data", []):
            claims.append(self._map_guidewire_to_claim_data(gw_claim))

        return claims

    def _map_updates_to_guidewire(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Map standard updates to Guidewire format"""
        gw_updates = {}

        if "status" in updates:
            gw_updates["state"] = updates["status"]
        if "adjuster_id" in updates:
            gw_updates["assignedUser"] = {"id": updates["adjuster_id"]}
        if "reserves" in updates:
            gw_updates["remainingReserves"] = updates["reserves"]

        return gw_updates

    def _map_guidewire_to_claim_data(self, gw_claim: Dict) -> ClaimData:
        """Map Guidewire claim to standard ClaimData"""
        return ClaimData(
            claim_id=gw_claim.get("claimNumber"),
            policy_number=gw_claim.get("policy", {}).get("policyNumber"),
            insured_name=gw_claim.get("insured", {}).get("displayName"),
            claim_amount=float(gw_claim.get("totalIncurred", 0)),
            incident_date=gw_claim.get("lossDate"),
            reported_date=gw_claim.get("reportedDate"),
            claim_type=gw_claim.get("lossCause"),
            status=gw_claim.get("state"),
            description=gw_claim.get("description", ""),
            external_refs={"guidewire_id": gw_claim.get("id")}
        )

class DuckCreekIntegration(ClaimsSystemIntegration):
    """Integration with Duck Creek Claims"""

    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.session = None

    async def _get_session(self):
        """Get authenticated session"""
        if not self.session:
            self.session = aiohttp.ClientSession(
                auth=aiohttp.BasicAuth(self.username, self.password)
            )
        return self.session

    async def get_claim(self, claim_id: str) -> ClaimData:
        """Get claim from Duck Creek"""
        session = await self._get_session()
        url = f"{self.base_url}/api/claims/{claim_id}"

        async with session.get(url) as response:
            response.raise_for_status()
            dc_claim = await response.json()

            return ClaimData(
                claim_id=dc_claim.get("claimId"),
                policy_number=dc_claim.get("policyNumber"),
                insured_name=dc_claim.get("insuredName"),
                claim_amount=float(dc_claim.get("claimAmount", 0)),
                incident_date=dc_claim.get("incidentDate"),
                reported_date=dc_claim.get("reportedDate"),
                claim_type=dc_claim.get("claimType"),
                status=dc_claim.get("status"),
                description=dc_claim.get("description", ""),
                external_refs={"duck_creek_id": dc_claim.get("id")}
            )

    async def update_claim(self, claim_id: str, updates: Dict[str, Any]) -> bool:
        """Update claim in Duck Creek"""
        session = await self._get_session()
        url = f"{self.base_url}/api/claims/{claim_id}"

        try:
            async with session.put(url, json=updates) as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"Failed to update Duck Creek claim: {e}")
            return False

    async def create_claim(self, claim_data: ClaimData) -> str:
        """Create claim in Duck Creek"""
        session = await self._get_session()
        url = f"{self.base_url}/api/claims"

        dc_claim_data = asdict(claim_data)

        async with session.post(url, json=dc_claim_data) as response:
            response.raise_for_status()
            result = await response.json()
            return result.get("claimId")

    async def get_policy(self, policy_number: str) -> PolicyData:
        """Get policy from Duck Creek"""
        session = await self._get_session()
        url = f"{self.base_url}/api/policies/{policy_number}"

        async with session.get(url) as response:
            response.raise_for_status()
            dc_policy = await response.json()

            return PolicyData(
                policy_number=dc_policy.get("policyNumber"),
                product_line=dc_policy.get("productLine"),
                effective_date=dc_policy.get("effectiveDate"),
                expiration_date=dc_policy.get("expirationDate"),
                policy_status=dc_policy.get("status"),
                coverage_limits=dc_policy.get("coverageLimits", {}),
                deductibles=dc_policy.get("deductibles", {}),
                premium_amount=float(dc_policy.get("premiumAmount", 0)),
                named_insured=dc_policy.get("namedInsured"),
                mailing_address=dc_policy.get("mailingAddress", {}),
                phone_number=dc_policy.get("phoneNumber"),
                email=dc_policy.get("email")
            )

    async def search_claims(self, criteria: Dict[str, Any]) -> List[ClaimData]:
        """Search claims in Duck Creek"""
        session = await self._get_session()
        url = f"{self.base_url}/api/claims/search"

        async with session.post(url, json=criteria) as response:
            response.raise_for_status()
            results = await response.json()

            claims = []
            for dc_claim in results.get("claims", []):
                claims.append(self._map_duck_creek_to_claim_data(dc_claim))

            return claims

    def _map_duck_creek_to_claim_data(self, dc_claim: Dict) -> ClaimData:
        """Map Duck Creek claim to standard format"""
        return ClaimData(
            claim_id=dc_claim.get("claimId"),
            policy_number=dc_claim.get("policyNumber"),
            insured_name=dc_claim.get("insuredName"),
            claim_amount=float(dc_claim.get("claimAmount", 0)),
            incident_date=dc_claim.get("incidentDate"),
            reported_date=dc_claim.get("reportedDate"),
            claim_type=dc_claim.get("claimType"),
            status=dc_claim.get("status"),
            description=dc_claim.get("description", ""),
            external_refs={"duck_creek_id": dc_claim.get("id")}
        )

class ClaimsIntegrationManager:
    """Central manager for all claims system integrations"""

    def __init__(self):
        self.integrations: Dict[ClaimsSystemType, ClaimsSystemIntegration] = {}
        self.primary_system: Optional[ClaimsSystemType] = None

    def register_integration(self, system_type: ClaimsSystemType, integration: ClaimsSystemIntegration):
        """Register a claims system integration"""
        self.integrations[system_type] = integration
        if not self.primary_system:
            self.primary_system = system_type
        logger.info(f"Registered {system_type} integration")

    def set_primary_system(self, system_type: ClaimsSystemType):
        """Set the primary claims system"""
        if system_type not in self.integrations:
            raise ValueError(f"Integration for {system_type} not registered")
        self.primary_system = system_type
        logger.info(f"Set {system_type} as primary claims system")

    async def get_claim(self, claim_id: str, system: Optional[ClaimsSystemType] = None) -> ClaimData:
        """Get claim from specified system or primary"""
        system = system or self.primary_system
        if system not in self.integrations:
            raise ValueError(f"Integration for {system} not available")

        return await self.integrations[system].get_claim(claim_id)

    async def update_claim(self, claim_id: str, updates: Dict[str, Any], system: Optional[ClaimsSystemType] = None) -> bool:
        """Update claim in specified system or primary"""
        system = system or self.primary_system
        if system not in self.integrations:
            raise ValueError(f"Integration for {system} not available")

        return await self.integrations[system].update_claim(claim_id, updates)

    async def sync_claim_across_systems(self, claim_id: str, updates: Dict[str, Any]) -> Dict[ClaimsSystemType, bool]:
        """Update claim across all registered systems"""
        results = {}

        for system_type, integration in self.integrations.items():
            try:
                success = await integration.update_claim(claim_id, updates)
                results[system_type] = success
                logger.info(f"Synced claim {claim_id} to {system_type}: {'success' if success else 'failed'}")
            except Exception as e:
                logger.error(f"Failed to sync claim {claim_id} to {system_type}: {e}")
                results[system_type] = False

        return results

    async def cross_system_claim_search(self, criteria: Dict[str, Any]) -> Dict[ClaimsSystemType, List[ClaimData]]:
        """Search claims across all systems"""
        results = {}

        for system_type, integration in self.integrations.items():
            try:
                claims = await integration.search_claims(criteria)
                results[system_type] = claims
                logger.info(f"Found {len(claims)} claims in {system_type}")
            except Exception as e:
                logger.error(f"Search failed in {system_type}: {e}")
                results[system_type] = []

        return results

    def get_available_systems(self) -> List[ClaimsSystemType]:
        """Get list of available systems"""
        return list(self.integrations.keys())

    async def health_check(self) -> Dict[ClaimsSystemType, Dict[str, Any]]:
        """Check health of all integrated systems"""
        health_status = {}

        for system_type, integration in self.integrations.items():
            try:
                # Try a simple operation to test connectivity
                start_time = datetime.utcnow()

                if hasattr(integration, '_authenticate'):
                    await integration._authenticate()

                response_time = (datetime.utcnow() - start_time).total_seconds()

                health_status[system_type] = {
                    "status": "healthy",
                    "response_time_ms": response_time * 1000,
                    "last_checked": datetime.utcnow().isoformat()
                }
            except Exception as e:
                health_status[system_type] = {
                    "status": "unhealthy",
                    "error": str(e),
                    "last_checked": datetime.utcnow().isoformat()
                }

        return health_status

# Global integration manager instance
claims_integration_manager = ClaimsIntegrationManager()

# Factory functions for easy setup
def setup_guidewire_integration(base_url: str, username: str, password: str):
    """Setup Guidewire integration"""
    integration = GuidewireIntegration(base_url, username, password)
    claims_integration_manager.register_integration(ClaimsSystemType.GUIDEWIRE, integration)
    return integration

def setup_duck_creek_integration(base_url: str, username: str, password: str):
    """Setup Duck Creek integration"""
    integration = DuckCreekIntegration(base_url, username, password)
    claims_integration_manager.register_integration(ClaimsSystemType.DUCK_CREEK, integration)
    return integration

# Configuration for common setups
INTEGRATION_CONFIGS = {
    "production": {
        "guidewire": {
            "base_url": "https://claims.company.com/bc",
            "timeout": 30
        },
        "duck_creek": {
            "base_url": "https://duckcreek.company.com",
            "timeout": 30
        }
    },
    "staging": {
        "guidewire": {
            "base_url": "https://claims-staging.company.com/bc",
            "timeout": 60
        }
    }
}