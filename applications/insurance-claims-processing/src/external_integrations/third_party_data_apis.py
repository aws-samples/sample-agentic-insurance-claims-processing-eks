"""
Third-Party Data APIs Integration
Comprehensive integration with external data sources for enhanced claims processing
"""

import asyncio
import aiohttp
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from enum import Enum
from dataclasses import dataclass, asdict
import hashlib
from defusedxml import ElementTree as ET

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataSourceType(str, Enum):
    FRAUD_DATABASE = "fraud_database"
    VEHICLE_DATA = "vehicle_data"
    WEATHER_DATA = "weather_data"
    GEOLOCATION = "geolocation"
    SOCIAL_INTELLIGENCE = "social_intelligence"
    COURT_RECORDS = "court_records"
    CREDIT_REPORTS = "credit_reports"
    MEDICAL_RECORDS = "medical_records"
    PROPERTY_DATA = "property_data"

@dataclass
class FraudDatabaseResult:
    """Result from fraud database lookup"""
    person_matches: int
    vehicle_matches: int
    address_matches: int
    phone_matches: int
    previous_fraud_claims: List[Dict[str, Any]]
    risk_score: float
    network_connections: List[str]
    suspicious_patterns: List[str]

    # ISO ClaimSearch specific
    iso_claim_count: int
    iso_red_flags: List[str]

    # NICB specific
    nicb_stolen_vehicle: bool
    nicb_total_loss_history: List[Dict[str, Any]]

@dataclass
class VehicleDataResult:
    """Result from vehicle data lookup"""
    vin: str
    make: str
    model: str
    year: int
    trim: str

    # Valuation
    actual_cash_value: float
    replacement_cost: float

    # History
    accident_history: List[Dict[str, Any]]
    service_records: List[Dict[str, Any]]
    ownership_history: List[Dict[str, Any]]
    title_issues: List[str]

    # Safety & Recalls
    safety_ratings: Dict[str, Any]
    open_recalls: List[Dict[str, Any]]

    # Anti-theft
    anti_theft_devices: List[str]
    theft_history: List[Dict[str, Any]]

@dataclass
class WeatherDataResult:
    """Weather data for incident location/time"""
    location: Dict[str, Any]
    timestamp: str

    # Current conditions at time of incident
    temperature: float
    precipitation: float
    wind_speed: float
    visibility: float
    road_conditions: str

    # Alerts and warnings
    weather_alerts: List[str]
    severe_weather: bool

    # Historical data
    historical_average: Dict[str, float]
    anomaly_score: float

class ISOClaimSearchAPI:
    """Integration with ISO ClaimSearch fraud database"""

    def __init__(self, api_key: str, username: str, password: str):
        self.api_key = api_key
        self.username = username
        self.password = password
        self.base_url = "https://claimsearch.iso.com/api/v1"
        self.session = None

    async def _get_session(self):
        """Get authenticated session"""
        if not self.session:
            self.session = aiohttp.ClientSession(
                headers={
                    "X-API-Key": self.api_key,
                    "Content-Type": "application/json"
                },
                auth=aiohttp.BasicAuth(self.username, self.password)
            )
        return self.session

    async def search_person(self,
                          first_name: str,
                          last_name: str,
                          dob: Optional[str] = None,
                          ssn: Optional[str] = None) -> FraudDatabaseResult:
        """Search for person in ISO ClaimSearch"""
        session = await self._get_session()

        search_payload = {
            "search_type": "person",
            "criteria": {
                "first_name": first_name,
                "last_name": last_name,
                "date_of_birth": dob,
                "ssn": ssn
            },
            "include_related": True,
            "max_results": 100
        }

        async with session.post(f"{self.base_url}/search", json=search_payload) as response:
            response.raise_for_status()
            results = await response.json()

            return self._parse_iso_results(results)

    async def search_vehicle(self, vin: str) -> FraudDatabaseResult:
        """Search for vehicle in ISO ClaimSearch"""
        session = await self._get_session()

        search_payload = {
            "search_type": "vehicle",
            "criteria": {"vin": vin},
            "include_related": True
        }

        async with session.post(f"{self.base_url}/search", json=search_payload) as response:
            response.raise_for_status()
            results = await response.json()

            return self._parse_iso_results(results)

    def _parse_iso_results(self, results: Dict) -> FraudDatabaseResult:
        """Parse ISO ClaimSearch results"""
        claims_data = results.get("claims", [])
        person_data = results.get("persons", [])
        vehicle_data = results.get("vehicles", [])

        # Calculate risk score based on claim frequency and patterns
        claim_count = len(claims_data)
        recent_claims = [c for c in claims_data
                        if datetime.fromisoformat(c.get("loss_date", "2020-01-01")) >
                        datetime.now() - timedelta(days=730)]

        risk_score = min(1.0, (claim_count * 0.1) + (len(recent_claims) * 0.2))

        # Identify suspicious patterns
        suspicious_patterns = []
        if claim_count > 5:
            suspicious_patterns.append("High claim frequency")
        if len(recent_claims) > 2:
            suspicious_patterns.append("Recent high activity")

        # Extract red flags
        red_flags = []
        for claim in claims_data:
            if claim.get("questionable_claim_indicator"):
                red_flags.append("Questionable claim indicator")
            if claim.get("investigation_flag"):
                red_flags.append("Investigation required")

        return FraudDatabaseResult(
            person_matches=len(person_data),
            vehicle_matches=len(vehicle_data),
            address_matches=len(set(p.get("address") for p in person_data)),
            phone_matches=len(set(p.get("phone") for p in person_data)),
            previous_fraud_claims=claims_data,
            risk_score=risk_score,
            network_connections=[],  # Would analyze relationships
            suspicious_patterns=suspicious_patterns,
            iso_claim_count=claim_count,
            iso_red_flags=red_flags,
            nicb_stolen_vehicle=False,  # Not available in ISO
            nicb_total_loss_history=[]
        )

class CarfaxAPI:
    """Integration with Carfax vehicle history"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.carfax.com/v1"
        self.session = None

    async def _get_session(self):
        if not self.session:
            self.session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
            )
        return self.session

    async def get_vehicle_history(self, vin: str) -> VehicleDataResult:
        """Get comprehensive vehicle history from Carfax"""
        session = await self._get_session()

        async with session.get(f"{self.base_url}/vehicles/{vin}/history") as response:
            response.raise_for_status()
            carfax_data = await response.json()

            return self._parse_carfax_data(vin, carfax_data)

    def _parse_carfax_data(self, vin: str, data: Dict) -> VehicleDataResult:
        """Parse Carfax vehicle data"""
        vehicle_info = data.get("vehicle", {})
        history_events = data.get("history_events", [])

        # Parse accident history
        accidents = [event for event in history_events
                    if event.get("event_type") == "accident"]

        # Parse service records
        services = [event for event in history_events
                   if event.get("event_type") == "service"]

        # Parse ownership history
        ownership = [event for event in history_events
                    if event.get("event_type") == "ownership_change"]

        # Identify title issues
        title_issues = []
        for event in history_events:
            if event.get("title_problem"):
                title_issues.append(event.get("description"))

        return VehicleDataResult(
            vin=vin,
            make=vehicle_info.get("make", ""),
            model=vehicle_info.get("model", ""),
            year=vehicle_info.get("year", 0),
            trim=vehicle_info.get("trim", ""),
            actual_cash_value=vehicle_info.get("current_value", 0.0),
            replacement_cost=vehicle_info.get("replacement_cost", 0.0),
            accident_history=accidents,
            service_records=services,
            ownership_history=ownership,
            title_issues=title_issues,
            safety_ratings=vehicle_info.get("safety_ratings", {}),
            open_recalls=vehicle_info.get("recalls", []),
            anti_theft_devices=vehicle_info.get("anti_theft", []),
            theft_history=[]  # Would be populated from theft database
        )

class WeatherUndergroundAPI:
    """Integration with Weather Underground historical weather data"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.weather.com/v1"
        self.session = None

    async def _get_session(self):
        if not self.session:
            self.session = aiohttp.ClientSession()
        return self.session

    async def get_historical_weather(self,
                                   latitude: float,
                                   longitude: float,
                                   incident_datetime: str) -> WeatherDataResult:
        """Get historical weather for incident location and time"""
        session = await self._get_session()

        # Parse incident datetime
        incident_dt = datetime.fromisoformat(incident_datetime.replace('Z', '+00:00'))
        date_str = incident_dt.strftime("%Y%m%d")

        # Historical weather API call
        url = f"{self.base_url}/location/{latitude},{longitude}/date/{date_str}/history.json"
        params = {
            "apikey": self.api_key,
            "language": "en-US",
            "units": "e"  # English units
        }

        async with session.get(url, params=params) as response:
            response.raise_for_status()
            weather_data = await response.json()

            return self._parse_weather_data(latitude, longitude, incident_datetime, weather_data)

    def _parse_weather_data(self, lat: float, lon: float, timestamp: str, data: Dict) -> WeatherDataResult:
        """Parse weather data response"""
        observations = data.get("observations", [])

        # Find closest observation to incident time
        target_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        closest_obs = None
        min_diff = float('inf')

        for obs in observations:
            obs_time = datetime.fromisoformat(obs.get("valid_time_gmt"))
            diff = abs((target_time - obs_time).total_seconds())
            if diff < min_diff:
                min_diff = diff
                closest_obs = obs

        if not closest_obs:
            # Return default/unknown weather
            return WeatherDataResult(
                location={"latitude": lat, "longitude": lon},
                timestamp=timestamp,
                temperature=0.0,
                precipitation=0.0,
                wind_speed=0.0,
                visibility=10.0,
                road_conditions="unknown",
                weather_alerts=[],
                severe_weather=False,
                historical_average={},
                anomaly_score=0.0
            )

        # Determine road conditions
        temp = closest_obs.get("temp", 50)
        precip = closest_obs.get("precip_hrly", 0)
        wind = closest_obs.get("wspd", 0)

        road_conditions = "clear"
        if precip > 0.1:
            if temp < 32:
                road_conditions = "icy"
            else:
                road_conditions = "wet"
        elif wind > 25:
            road_conditions = "windy"

        # Check for severe weather
        severe_weather = (precip > 0.5 or wind > 30 or
                         closest_obs.get("vis", 10) < 2)

        weather_alerts = []
        if severe_weather:
            weather_alerts.append("Severe weather conditions at time of incident")

        return WeatherDataResult(
            location={"latitude": lat, "longitude": lon},
            timestamp=timestamp,
            temperature=temp,
            precipitation=precip,
            wind_speed=wind,
            visibility=closest_obs.get("vis", 10),
            road_conditions=road_conditions,
            weather_alerts=weather_alerts,
            severe_weather=severe_weather,
            historical_average={
                "temperature": data.get("almanac", {}).get("temp_normal", temp),
                "precipitation": data.get("almanac", {}).get("precip_normal", precip)
            },
            anomaly_score=0.0  # Would calculate based on historical norms
        )

class GoogleMapsAPI:
    """Integration with Google Maps for geolocation and route analysis"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://maps.googleapis.com/maps/api"
        self.session = None

    async def _get_session(self):
        if not self.session:
            self.session = aiohttp.ClientSession()
        return self.session

    async def geocode_address(self, address: str) -> Dict[str, Any]:
        """Convert address to coordinates"""
        session = await self._get_session()

        params = {
            "address": address,
            "key": self.api_key
        }

        async with session.get(f"{self.base_url}/geocode/json", params=params) as response:
            response.raise_for_status()
            data = await response.json()

            if data.get("status") == "OK" and data.get("results"):
                result = data["results"][0]
                location = result["geometry"]["location"]

                return {
                    "latitude": location["lat"],
                    "longitude": location["lng"],
                    "formatted_address": result["formatted_address"],
                    "address_components": result["address_components"],
                    "place_id": result["place_id"]
                }

            return {}

    async def get_route_analysis(self, origin: str, destination: str, incident_time: str) -> Dict[str, Any]:
        """Analyze route between two points"""
        session = await self._get_session()

        params = {
            "origin": origin,
            "destination": destination,
            "departure_time": incident_time,
            "traffic_model": "best_guess",
            "key": self.api_key
        }

        async with session.get(f"{self.base_url}/directions/json", params=params) as response:
            response.raise_for_status()
            data = await response.json()

            if data.get("status") == "OK" and data.get("routes"):
                route = data["routes"][0]
                leg = route["legs"][0]

                return {
                    "distance_miles": leg["distance"]["value"] * 0.000621371,
                    "duration_minutes": leg["duration"]["value"] / 60,
                    "duration_in_traffic_minutes": leg.get("duration_in_traffic", {}).get("value", 0) / 60,
                    "route_feasible": True,
                    "traffic_conditions": "moderate" if leg.get("duration_in_traffic") else "unknown",
                    "waypoints": [step["start_location"] for step in leg["steps"]]
                }

            return {"route_feasible": False}

class ThirdPartyDataManager:
    """Central manager for all third-party data integrations"""

    def __init__(self):
        self.integrations: Dict[DataSourceType, Any] = {}
        self.cache: Dict[str, Any] = {}
        self.cache_ttl: Dict[str, datetime] = {}

    def register_fraud_database(self, api_key: str, username: str, password: str):
        """Register ISO ClaimSearch integration"""
        self.integrations[DataSourceType.FRAUD_DATABASE] = ISOClaimSearchAPI(api_key, username, password)

    def register_vehicle_data(self, api_key: str):
        """Register Carfax integration"""
        self.integrations[DataSourceType.VEHICLE_DATA] = CarfaxAPI(api_key)

    def register_weather_data(self, api_key: str):
        """Register Weather Underground integration"""
        self.integrations[DataSourceType.WEATHER_DATA] = WeatherUndergroundAPI(api_key)

    def register_geolocation(self, api_key: str):
        """Register Google Maps integration"""
        self.integrations[DataSourceType.GEOLOCATION] = GoogleMapsAPI(api_key)

    def _get_cache_key(self, operation: str, **kwargs) -> str:
        """Generate cache key for operation"""
        key_data = f"{operation}:{json.dumps(kwargs, sort_keys=True)}"
        return hashlib.sha256(key_data.encode()).hexdigest()

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid"""
        if cache_key not in self.cache_ttl:
            return False
        return datetime.utcnow() < self.cache_ttl[cache_key]

    def _cache_result(self, cache_key: str, result: Any, ttl_minutes: int = 60):
        """Cache result with TTL"""
        self.cache[cache_key] = result
        self.cache_ttl[cache_key] = datetime.utcnow() + timedelta(minutes=ttl_minutes)

    async def comprehensive_fraud_check(self,
                                      claim_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive fraud check across all sources"""
        results = {}

        # Person fraud check
        if "claimant_name" in claim_data:
            name_parts = claim_data["claimant_name"].split()
            if len(name_parts) >= 2:
                cache_key = self._get_cache_key("fraud_person",
                                              first_name=name_parts[0],
                                              last_name=name_parts[-1])

                if self._is_cache_valid(cache_key):
                    results["person_fraud_check"] = self.cache[cache_key]
                elif DataSourceType.FRAUD_DATABASE in self.integrations:
                    try:
                        fraud_result = await self.integrations[DataSourceType.FRAUD_DATABASE].search_person(
                            first_name=name_parts[0],
                            last_name=name_parts[-1],
                            dob=claim_data.get("claimant_dob")
                        )
                        results["person_fraud_check"] = asdict(fraud_result)
                        self._cache_result(cache_key, results["person_fraud_check"], 120)  # 2 hour cache
                    except Exception as e:
                        logger.error(f"Fraud database person search failed: {e}")
                        results["person_fraud_check"] = {"error": str(e)}

        # Vehicle fraud check
        if "vehicle_vin" in claim_data and DataSourceType.FRAUD_DATABASE in self.integrations:
            cache_key = self._get_cache_key("fraud_vehicle", vin=claim_data["vehicle_vin"])

            if self._is_cache_valid(cache_key):
                results["vehicle_fraud_check"] = self.cache[cache_key]
            else:
                try:
                    fraud_result = await self.integrations[DataSourceType.FRAUD_DATABASE].search_vehicle(
                        claim_data["vehicle_vin"]
                    )
                    results["vehicle_fraud_check"] = asdict(fraud_result)
                    self._cache_result(cache_key, results["vehicle_fraud_check"], 240)  # 4 hour cache
                except Exception as e:
                    logger.error(f"Fraud database vehicle search failed: {e}")
                    results["vehicle_fraud_check"] = {"error": str(e)}

        return results

    async def comprehensive_vehicle_analysis(self, vin: str) -> Dict[str, Any]:
        """Get comprehensive vehicle data"""
        cache_key = self._get_cache_key("vehicle_analysis", vin=vin)

        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]

        results = {}

        if DataSourceType.VEHICLE_DATA in self.integrations:
            try:
                vehicle_data = await self.integrations[DataSourceType.VEHICLE_DATA].get_vehicle_history(vin)
                results["vehicle_history"] = asdict(vehicle_data)
            except Exception as e:
                logger.error(f"Vehicle data lookup failed: {e}")
                results["vehicle_history"] = {"error": str(e)}

        # Also check fraud database for vehicle
        if DataSourceType.FRAUD_DATABASE in self.integrations:
            try:
                fraud_check = await self.integrations[DataSourceType.FRAUD_DATABASE].search_vehicle(vin)
                results["fraud_check"] = asdict(fraud_check)
            except Exception as e:
                logger.error(f"Vehicle fraud check failed: {e}")
                results["fraud_check"] = {"error": str(e)}

        self._cache_result(cache_key, results, 360)  # 6 hour cache
        return results

    async def incident_environment_analysis(self,
                                          location: str,
                                          incident_datetime: str) -> Dict[str, Any]:
        """Analyze environmental conditions at time of incident"""
        results = {}

        # Geocode location first
        if DataSourceType.GEOLOCATION in self.integrations:
            try:
                geo_data = await self.integrations[DataSourceType.GEOLOCATION].geocode_address(location)
                results["location_data"] = geo_data

                # Get weather data if we have coordinates
                if geo_data and DataSourceType.WEATHER_DATA in self.integrations:
                    weather_data = await self.integrations[DataSourceType.WEATHER_DATA].get_historical_weather(
                        latitude=geo_data["latitude"],
                        longitude=geo_data["longitude"],
                        incident_datetime=incident_datetime
                    )
                    results["weather_data"] = asdict(weather_data)

            except Exception as e:
                logger.error(f"Environment analysis failed: {e}")
                results["error"] = str(e)

        return results

    async def health_check(self) -> Dict[DataSourceType, Dict[str, Any]]:
        """Check health of all third-party integrations"""
        health_status = {}

        for source_type, integration in self.integrations.items():
            try:
                start_time = datetime.utcnow()

                # Test with a simple operation
                if source_type == DataSourceType.FRAUD_DATABASE:
                    # Test authentication or basic call
                    await integration._get_session()
                elif source_type == DataSourceType.GEOLOCATION:
                    # Test geocoding with a simple address
                    await integration.geocode_address("1600 Amphitheatre Parkway, Mountain View, CA")

                response_time = (datetime.utcnow() - start_time).total_seconds()

                health_status[source_type] = {
                    "status": "healthy",
                    "response_time_ms": response_time * 1000,
                    "last_checked": datetime.utcnow().isoformat()
                }
            except Exception as e:
                health_status[source_type] = {
                    "status": "unhealthy",
                    "error": str(e),
                    "last_checked": datetime.utcnow().isoformat()
                }

        return health_status

# Global third-party data manager
third_party_data_manager = ThirdPartyDataManager()

# Configuration helper
def setup_production_integrations(config: Dict[str, Dict[str, str]]):
    """Setup all production integrations from config"""

    if "iso_claimsearch" in config:
        iso_config = config["iso_claimsearch"]
        third_party_data_manager.register_fraud_database(
            api_key=iso_config["api_key"],
            username=iso_config["username"],
            password=iso_config["password"]
        )

    if "carfax" in config:
        third_party_data_manager.register_vehicle_data(
            api_key=config["carfax"]["api_key"]
        )

    if "weather_underground" in config:
        third_party_data_manager.register_weather_data(
            api_key=config["weather_underground"]["api_key"]
        )

    if "google_maps" in config:
        third_party_data_manager.register_geolocation(
            api_key=config["google_maps"]["api_key"]
        )

    logger.info("Production third-party integrations configured")

# Example configuration
# IMPORTANT: These are PLACEHOLDER values only. Replace with actual credentials from your secure secrets management system.
# Do NOT use these values in production. See docs/SECRETS_MANAGEMENT.md for secure credential management.
SAMPLE_CONFIG = {
    "iso_claimsearch": {
        "api_key": "<ISO_API_KEY>",
        "username": "<ISO_USERNAME>",
        "password": "<ISO_PASSWORD>"
    },
    "carfax": {
        "api_key": "<CARFAX_API_KEY>"
    },
    "weather_underground": {
        "api_key": "<WEATHER_API_KEY>"
    },
    "google_maps": {
        "api_key": "<GOOGLE_MAPS_API_KEY>"
    }
}