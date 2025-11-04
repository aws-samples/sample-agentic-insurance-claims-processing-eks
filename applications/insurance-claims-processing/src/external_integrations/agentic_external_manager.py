"""
Agentic External Data Manager - FREE Demo Mode
Sophisticated simulated external data for agentic AI demonstrations
"""

import asyncio
import json
import logging
import random
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

# Use cryptographically secure random for security-sensitive operations
secure_random = secrets.SystemRandom()

class DataSourceType(str, Enum):
    FRAUD_DATABASE = "fraud_database"
    VEHICLE_DATA = "vehicle_data"
    WEATHER_DATA = "weather_data"
    GEOLOCATION = "geolocation"
    IDENTITY_VERIFICATION = "identity_verification"
    COURT_RECORDS = "court_records"
    PROPERTY_DATA = "property_data"

@dataclass
class ExternalDataResult:
    """Unified external data result"""
    source: str
    data: Dict[str, Any]
    confidence: float
    processing_time_ms: int
    risk_indicators: List[str]
    agentic_insights: List[str]

class AgenticExternalDataManager:
    """
    🤖 AGENTIC AI DEMO MODE - FREE EXTERNAL DATA SIMULATION

    Simulates sophisticated multi-source data integration that would
    normally cost $100K+/year from real providers. Perfect for demos!
    """

    def __init__(self):
        self.demo_mode = True  # Always FREE demo mode
        self.processing_stats = {
            "total_queries": 0,
            "successful_queries": 0,
            "avg_processing_time": 0
        }
        logger.info("🤖 Agentic External Data Manager - FREE DEMO MODE activated")

    async def comprehensive_claim_enrichment(self, claim_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        🎯 Main entry point: Comprehensive multi-source claim enrichment
        Demonstrates agentic AI decision-making across multiple data sources
        """
        start_time = datetime.now()
        enriched_data = {}

        # Agentic decision: Determine which data sources to query
        data_sources = await self._agentic_source_selection(claim_data)

        logger.info(f"🤖 Agentic AI selected {len(data_sources)} data sources for enrichment")

        # Parallel data fetching (agentic efficiency)
        tasks = []
        for source in data_sources:
            if source == DataSourceType.FRAUD_DATABASE:
                tasks.append(self._get_fraud_intelligence(claim_data))
            elif source == DataSourceType.VEHICLE_DATA:
                tasks.append(self._get_vehicle_intelligence(claim_data))
            elif source == DataSourceType.WEATHER_DATA:
                tasks.append(self._get_weather_intelligence(claim_data))
            elif source == DataSourceType.GEOLOCATION:
                tasks.append(self._get_location_intelligence(claim_data))
            elif source == DataSourceType.IDENTITY_VERIFICATION:
                tasks.append(self._get_identity_intelligence(claim_data))

        # Execute all data fetching concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Compile enriched data
        for i, result in enumerate(results):
            if isinstance(result, ExternalDataResult):
                enriched_data[data_sources[i]] = result

        # Agentic analysis and correlation
        agentic_analysis = await self._agentic_correlation_analysis(enriched_data, claim_data)

        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        return {
            "external_data_sources": enriched_data,
            "agentic_analysis": agentic_analysis,
            "processing_metadata": {
                "sources_queried": len(data_sources),
                "successful_sources": len([r for r in results if isinstance(r, ExternalDataResult)]),
                "processing_time_ms": processing_time,
                "cost": "$0.00 (DEMO MODE)",
                "agentic_efficiency": "95%"
            }
        }

    async def _agentic_source_selection(self, claim_data: Dict[str, Any]) -> List[DataSourceType]:
        """Agentic AI decides which external data sources are needed"""
        sources = []
        claim_amount = claim_data.get("claim_amount", 0)
        claim_type = claim_data.get("claim_type", "")

        # Always check fraud database (industry standard)
        sources.append(DataSourceType.FRAUD_DATABASE)

        # Agentic reasoning for vehicle data
        if any(vehicle_term in claim_type.lower() for vehicle_term in ["collision", "comprehensive", "auto", "vehicle"]):
            sources.append(DataSourceType.VEHICLE_DATA)

        # Agentic reasoning for weather data
        if any(weather_term in claim_type.lower() for weather_term in ["storm", "hail", "flood", "wind", "weather"]):
            sources.append(DataSourceType.WEATHER_DATA)

        # High-value claims get full treatment
        if claim_amount > 25000:
            sources.extend([
                DataSourceType.GEOLOCATION,
                DataSourceType.IDENTITY_VERIFICATION
            ])

        logger.info(f"🤖 Agentic source selection: {sources}")
        return sources

    async def _get_fraud_intelligence(self, claim_data: Dict[str, Any]) -> ExternalDataResult:
        """Simulate sophisticated fraud database lookup (ISO ClaimSearch equivalent)"""
        await asyncio.sleep(0.2)  # Simulate API call time

        claim_amount = claim_data.get("claim_amount", 0)
        customer_name = claim_data.get("customer_name", "")

        # Sophisticated fraud simulation based on claim characteristics
        base_risk = secure_random.uniform(0.1, 0.4)

        # Adjust risk based on claim amount
        if claim_amount > 75000:
            base_risk += 0.3
        elif claim_amount > 50000:
            base_risk += 0.2
        elif claim_amount > 25000:
            base_risk += 0.1

        # Simulate previous claims
        previous_claims = secure_random.randint(0, 5) if base_risk > 0.4 else secure_random.randint(0, 2)

        fraud_data = {
            "iso_claimsearch_results": {
                "previous_claims_count": previous_claims,
                "total_claim_amount": previous_claims * secure_random.uniform(5000, 25000),
                "claim_frequency_score": min(1.0, previous_claims / 3.0),
                "network_connections": self._generate_network_connections(base_risk),
                "suspicious_patterns": self._generate_suspicious_patterns(base_risk),
                "fraud_indicators": self._generate_fraud_indicators(base_risk)
            },
            "nicb_database": {
                "stolen_vehicle_check": "clear" if base_risk < 0.6 else "flagged",
                "total_loss_history": secure_random.randint(0, 2) if base_risk > 0.5 else 0,
                "vin_verification": "verified" if base_risk < 0.7 else "discrepancy_found"
            },
            "lexisnexis_identity": {
                "identity_verification_score": max(0, 1.0 - base_risk),
                "address_stability": "stable" if base_risk < 0.5 else "unstable",
                "employment_verification": "verified" if base_risk < 0.6 else "unverified"
            }
        }

        risk_indicators = []
        if previous_claims > 3:
            risk_indicators.append("High claim frequency")
        if base_risk > 0.6:
            risk_indicators.append("Elevated fraud risk profile")
        if fraud_data["nicb_database"]["stolen_vehicle_check"] == "flagged":
            risk_indicators.append("Vehicle theft history")

        agentic_insights = [
            f"Fraud risk assessment: {'HIGH' if base_risk > 0.6 else 'MEDIUM' if base_risk > 0.3 else 'LOW'}",
            f"Recommended action: {'SIU escalation' if base_risk > 0.7 else 'Standard processing' if base_risk < 0.4 else 'Enhanced review'}",
            f"Previous claims pattern: {'Concerning' if previous_claims > 2 else 'Normal'}"
        ]

        return ExternalDataResult(
            source="fraud_database",
            data=fraud_data,
            confidence=0.95,
            processing_time_ms=secure_random.randint(180, 350),
            risk_indicators=risk_indicators,
            agentic_insights=agentic_insights
        )

    async def _get_vehicle_intelligence(self, claim_data: Dict[str, Any]) -> ExternalDataResult:
        """Simulate comprehensive vehicle data (Carfax/AutoCheck equivalent)"""
        await asyncio.sleep(0.15)  # Simulate API call time

        vehicle_data = {
            "carfax_report": {
                "vehicle_history": {
                    "previous_owners": secure_random.randint(1, 4),
                    "accident_history": secure_random.randint(0, 3),
                    "service_records": secure_random.randint(5, 25),
                    "title_issues": secure_random.choice(["clean", "salvage", "flood", "lemon"]) if secure_random.random() > 0.8 else "clean"
                },
                "market_value": {
                    "kbb_value": claim_data.get("claim_amount", 0) * secure_random.uniform(0.8, 1.2),
                    "market_range_low": claim_data.get("claim_amount", 0) * 0.7,
                    "market_range_high": claim_data.get("claim_amount", 0) * 1.3,
                    "depreciation_rate": secure_random.uniform(10, 25)
                },
                "recall_information": {
                    "active_recalls": secure_random.randint(0, 3),
                    "safety_recalls": secure_random.randint(0, 2),
                    "compliance_status": secure_random.choice(["compliant", "pending_recall", "non_compliant"])
                }
            },
            "autocheck_score": secure_random.randint(75, 99),
            "vehicle_specifications": {
                "safety_rating": secure_random.randint(3, 5),
                "theft_rating": secure_random.choice(["low", "medium", "high"]),
                "repair_cost_index": secure_random.uniform(0.8, 1.5)
            }
        }

        risk_indicators = []
        agentic_insights = []

        if vehicle_data["carfax_report"]["vehicle_history"]["accident_history"] > 2:
            risk_indicators.append("Multiple previous accidents")
            agentic_insights.append("Vehicle accident history may affect claim validity")

        if vehicle_data["carfax_report"]["vehicle_history"]["title_issues"] != "clean":
            risk_indicators.append(f"Title issue: {vehicle_data['carfax_report']['vehicle_history']['title_issues']}")
            agentic_insights.append("Title status requires additional verification")

        kbb_value = vehicle_data["carfax_report"]["market_value"]["kbb_value"]
        claim_amount = claim_data.get("claim_amount", 0)
        if claim_amount > kbb_value * 1.1:
            risk_indicators.append("Claim amount exceeds vehicle value")
            agentic_insights.append("Claim amount validation recommended")

        return ExternalDataResult(
            source="vehicle_data",
            data=vehicle_data,
            confidence=0.92,
            processing_time_ms=secure_random.randint(120, 280),
            risk_indicators=risk_indicators,
            agentic_insights=agentic_insights
        )

    async def _get_weather_intelligence(self, claim_data: Dict[str, Any]) -> ExternalDataResult:
        """Simulate weather data verification (Weather Underground equivalent)"""
        await asyncio.sleep(0.1)  # Simulate API call time

        incident_date = claim_data.get("incident_date", datetime.now().isoformat())

        # Simulate weather conditions based on claim type
        claim_type = claim_data.get("claim_type", "").lower()

        if "storm" in claim_type or "hail" in claim_type:
            weather_severity = secure_random.uniform(0.6, 1.0)
            weather_condition = secure_random.choice(["severe_thunderstorm", "hailstorm", "tornado_watch"])
        elif "flood" in claim_type:
            weather_severity = secure_random.uniform(0.7, 1.0)
            weather_condition = "heavy_rain"
        else:
            weather_severity = secure_random.uniform(0.0, 0.4)
            weather_condition = secure_random.choice(["clear", "partly_cloudy", "light_rain"])

        weather_data = {
            "weather_underground": {
                "historical_conditions": {
                    "temperature_f": secure_random.randint(35, 95),
                    "humidity_percent": secure_random.randint(30, 90),
                    "wind_speed_mph": secure_random.randint(5, 40) if weather_severity > 0.5 else secure_random.randint(0, 15),
                    "precipitation_inches": weather_severity * secure_random.uniform(0, 4),
                    "visibility_miles": secure_random.uniform(0.5, 10) if weather_severity > 0.6 else 10,
                    "weather_condition": weather_condition
                },
                "severe_weather_alerts": {
                    "active_warnings": weather_severity > 0.7,
                    "warning_type": "severe_thunderstorm" if weather_severity > 0.7 else None,
                    "warning_duration_hours": secure_random.randint(2, 8) if weather_severity > 0.7 else 0
                },
                "climatology": {
                    "typical_conditions": "normal" if weather_severity < 0.5 else "unusual",
                    "historical_severity_rank": f"{int(weather_severity * 100)}th percentile"
                }
            }
        }

        risk_indicators = []
        agentic_insights = []

        if weather_severity > 0.7:
            risk_indicators.append("Severe weather conditions confirmed")
            agentic_insights.append("Weather supports claim circumstances")
        elif weather_severity < 0.2 and any(term in claim_type for term in ["storm", "hail", "weather"]):
            risk_indicators.append("Weather inconsistent with claim type")
            agentic_insights.append("Weather verification raises questions about claim")

        return ExternalDataResult(
            source="weather_data",
            data=weather_data,
            confidence=0.98,
            processing_time_ms=secure_random.randint(80, 150),
            risk_indicators=risk_indicators,
            agentic_insights=agentic_insights
        )

    async def _get_location_intelligence(self, claim_data: Dict[str, Any]) -> ExternalDataResult:
        """Simulate geolocation and route analysis"""
        await asyncio.sleep(0.12)  # Simulate API call time

        location_data = {
            "google_maps": {
                "incident_location": {
                    "address_verified": secure_random.choice([True, False]),
                    "coordinates": {
                        "latitude": secure_random.uniform(32.0, 42.0),
                        "longitude": secure_random.uniform(-120.0, -74.0)
                    },
                    "location_type": secure_random.choice(["street", "parking_lot", "highway", "residential"]),
                    "traffic_conditions": secure_random.choice(["light", "moderate", "heavy"])
                },
                "route_analysis": {
                    "route_feasible": True,
                    "typical_drive_time": secure_random.randint(15, 120),
                    "distance_miles": secure_random.uniform(5, 50),
                    "alternative_routes": secure_random.randint(2, 5)
                },
                "area_intelligence": {
                    "crime_rate": secure_random.choice(["low", "medium", "high"]),
                    "accident_frequency": secure_random.uniform(0.1, 2.5),
                    "fraud_hotspot": secure_random.choice([True, False])
                }
            }
        }

        risk_indicators = []
        agentic_insights = []

        if location_data["google_maps"]["area_intelligence"]["fraud_hotspot"]:
            risk_indicators.append("Location identified as fraud hotspot")
            agentic_insights.append("Geographic risk factor requires enhanced review")

        if not location_data["google_maps"]["incident_location"]["address_verified"]:
            risk_indicators.append("Address verification failed")
            agentic_insights.append("Location inconsistencies detected")

        return ExternalDataResult(
            source="geolocation",
            data=location_data,
            confidence=0.89,
            processing_time_ms=secure_random.randint(100, 200),
            risk_indicators=risk_indicators,
            agentic_insights=agentic_insights
        )

    async def _get_identity_intelligence(self, claim_data: Dict[str, Any]) -> ExternalDataResult:
        """Simulate identity verification and background checks"""
        await asyncio.sleep(0.18)  # Simulate API call time

        identity_data = {
            "lexisnexis": {
                "identity_verification": {
                    "name_verification": secure_random.choice(["verified", "partial_match", "no_match"]),
                    "address_verification": secure_random.choice(["verified", "historical_match", "no_match"]),
                    "phone_verification": secure_random.choice(["verified", "disconnected", "no_match"]),
                    "ssn_verification": secure_random.choice(["verified", "issued_different_state", "invalid"])
                },
                "background_information": {
                    "employment_history": secure_random.randint(1, 8),
                    "address_stability": secure_random.uniform(0.3, 1.0),
                    "financial_indicators": secure_random.choice(["stable", "declining", "stressed"]),
                    "public_records": secure_random.randint(0, 3)
                },
                "risk_assessment": {
                    "identity_confidence": secure_random.uniform(0.6, 1.0),
                    "synthetic_identity_risk": secure_random.uniform(0.0, 0.4),
                    "bust_out_risk": secure_random.uniform(0.0, 0.3)
                }
            }
        }

        risk_indicators = []
        agentic_insights = []

        if identity_data["lexisnexis"]["identity_verification"]["name_verification"] != "verified":
            risk_indicators.append("Identity verification concerns")
            agentic_insights.append("Additional identity documentation recommended")

        if identity_data["lexisnexis"]["risk_assessment"]["synthetic_identity_risk"] > 0.3:
            risk_indicators.append("Synthetic identity risk detected")
            agentic_insights.append("Enhanced identity verification required")

        return ExternalDataResult(
            source="identity_verification",
            data=identity_data,
            confidence=0.94,
            processing_time_ms=secure_random.randint(150, 300),
            risk_indicators=risk_indicators,
            agentic_insights=agentic_insights
        )

    async def _agentic_correlation_analysis(self, external_data: Dict[str, ExternalDataResult], claim_data: Dict[str, Any]) -> Dict[str, Any]:
        """Agentic AI performs sophisticated cross-source correlation analysis"""

        all_risk_indicators = []
        all_insights = []
        confidence_scores = []

        for source_type, result in external_data.items():
            all_risk_indicators.extend(result.risk_indicators)
            all_insights.extend(result.agentic_insights)
            confidence_scores.append(result.confidence)

        # Calculate composite risk score
        risk_count = len(all_risk_indicators)
        if risk_count == 0:
            composite_risk = 0.1
        elif risk_count <= 2:
            composite_risk = 0.3
        elif risk_count <= 4:
            composite_risk = 0.6
        else:
            composite_risk = 0.9

        # Agentic decision making
        if composite_risk > 0.7:
            recommendation = "SIU_ESCALATION"
            routing_decision = "Special Investigation Unit"
            confidence = "high"
        elif composite_risk > 0.4:
            recommendation = "ENHANCED_REVIEW"
            routing_decision = "Senior Claims Adjuster"
            confidence = "medium"
        else:
            recommendation = "STANDARD_PROCESSING"
            routing_decision = "Claims Adjuster"
            confidence = "high"

        return {
            "agentic_risk_assessment": {
                "composite_risk_score": composite_risk,
                "risk_level": "HIGH" if composite_risk > 0.6 else "MEDIUM" if composite_risk > 0.3 else "LOW",
                "confidence": confidence,
                "total_risk_indicators": risk_count
            },
            "agentic_recommendations": {
                "primary_recommendation": recommendation,
                "routing_decision": routing_decision,
                "additional_actions": self._generate_additional_actions(composite_risk),
                "estimated_processing_time": f"{secure_random.randint(2, 10)} business days"
            },
            "correlation_insights": {
                "cross_source_patterns": self._identify_patterns(external_data),
                "data_consistency": "high" if len(set(all_insights)) > 3 else "medium",
                "external_validation": f"{len(external_data)} sources consulted"
            },
            "all_risk_indicators": all_risk_indicators,
            "all_agentic_insights": all_insights
        }

    def _generate_network_connections(self, risk_level: float) -> List[str]:
        """Generate realistic fraud network connections"""
        if risk_level < 0.3:
            return []
        elif risk_level < 0.6:
            return secure_random.sample([
                "Shared address with previous claimant",
                "Phone number linked to multiple claims"
            ], secure_random.randint(0, 1))
        else:
            return secure_random.sample([
                "Shared address with previous claimant",
                "Phone number linked to multiple claims",
                "Vehicle registered to known fraud network",
                "Claims submitted from same IP address",
                "Repair shop flagged for fraud"
            ], secure_random.randint(1, 3))

    def _generate_suspicious_patterns(self, risk_level: float) -> List[str]:
        """Generate realistic suspicious patterns"""
        patterns = []
        if risk_level > 0.4:
            patterns.extend(secure_random.sample([
                "Claim timing near policy expiration",
                "Recent policy changes",
                "Multiple claims in short timeframe",
                "High-value claim relative to premium"
            ], secure_random.randint(1, 2)))
        if risk_level > 0.6:
            patterns.extend(secure_random.sample([
                "Weekend/holiday incident timing",
                "Delay in reporting incident",
                "Inconsistent story details",
                "Unusual damage patterns"
            ], secure_random.randint(1, 2)))
        return patterns

    def _generate_fraud_indicators(self, risk_level: float) -> List[str]:
        """Generate realistic fraud indicators"""
        if risk_level < 0.3:
            return []

        base_indicators = [
            "Prior insurance fraud conviction",
            "Bankruptcy filing within 2 years",
            "Multiple insurance companies",
            "Inconsistent employment history"
        ]

        return secure_random.sample(base_indicators, secure_random.randint(0, min(3, int(risk_level * 4))))

    def _generate_additional_actions(self, risk_level: float) -> List[str]:
        """Generate additional recommended actions"""
        if risk_level < 0.3:
            return ["Standard documentation review"]
        elif risk_level < 0.6:
            return [
                "Enhanced documentation required",
                "Secondary adjuster review",
                "Vehicle inspection mandatory"
            ]
        else:
            return [
                "Comprehensive investigation required",
                "Legal review recommended",
                "External expert evaluation",
                "Law enforcement notification consideration"
            ]

    def _identify_patterns(self, external_data: Dict[str, ExternalDataResult]) -> List[str]:
        """Identify cross-source patterns"""
        patterns = []

        if len(external_data) >= 3:
            patterns.append("Multi-source data correlation completed")

        risk_sources = [k for k, v in external_data.items() if len(v.risk_indicators) > 0]
        if len(risk_sources) >= 2:
            patterns.append("Risk indicators from multiple sources")

        return patterns

# Global instance for use across the application
agentic_external_manager = AgenticExternalDataManager()