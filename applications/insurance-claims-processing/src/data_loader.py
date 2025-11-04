"""
Synthetic Data Loader for Production-Grade Insurance Claims System
Loads realistic insurance data from the syntheticdatageneral files
"""

import csv
import zipfile
import os
import random
import secrets
from datetime import datetime, timedelta
from typing import List, Dict, Any
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

# Use cryptographically secure random for security-sensitive operations
secure_random = secrets.SystemRandom()

class SyntheticDataLoader:
    """Load synthetic insurance data into MongoDB"""

    def __init__(self, mongodb_url: str = None):
        if mongodb_url is None:
            mongodb_url = os.getenv(
                "MONGODB_URL",
                "mongodb://admin:<YOUR_MONGODB_PASSWORD>@mongodb-service.database.svc.cluster.local:27017/claims_db?authSource=admin"
            )
        self.mongodb_url = mongodb_url
        self.client = None
        self.db = None

    async def connect(self):
        """Connect to MongoDB"""
        self.client = AsyncIOMotorClient(self.mongodb_url)
        self.db = self.client.claims_db
        print("Connected to MongoDB")

    async def disconnect(self):
        """Disconnect from MongoDB"""
        if self.client:
            self.client.close()
            print("Disconnected from MongoDB")

    def extract_zip_file(self, zip_path: str, extract_to: str = "/tmp/synthetic_data"):
        """Extract synthetic data zip file"""
        print(f"Extracting {zip_path}...")
        os.makedirs(extract_to, exist_ok=True)

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)

        # Find extracted CSV files
        csv_files = []
        for root, dirs, files in os.walk(extract_to):
            for file in files:
                if file.endswith('.csv'):
                    csv_files.append(os.path.join(root, file))

        print(f"Found {len(csv_files)} CSV files")
        return csv_files

    def parse_policy_csv(self, csv_path: str, limit: int = 1000) -> List[Dict[str, Any]]:
        """Parse policy summary CSV file"""
        print(f"Parsing {csv_path}...")
        policies = []

        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                if i >= limit:
                    break

                try:
                    # Map CSV columns to our policy model
                    policy = {
                        "policy_number": row.get('Policy Number', '').strip(),
                        "policy_effective_date": self._parse_date(row.get('Policy Effective Date')),
                        "policy_expiration_date": self._parse_date(row.get('Policy Expiration Date')),
                        "line_of_business": row.get('Line of Business', 'Unknown'),
                        "lob_code": row.get('LOB Code', ''),
                        "policy_status": "Active",  # Default status
                        "policy_term": 12,  # Default term
                        "sum_assured": self._parse_float(row.get('Revenue', 0)) * 10,  # Estimate
                        "policy_premium": self._parse_float(row.get('Written Premium', 0)),
                        "primary_insured_customer_id": row.get('Company', '').strip()[:20],
                        "customer_no": row.get('Company', '').strip()[:20],
                        "sales_channel": row.get('Channel', 'Agent'),
                        "sales_agent_code": row.get('Agent Code', 'AG001'),
                        "issue_state": row.get('State', 'CA'),
                        "resident_state": row.get('State', 'CA'),
                        "issue_age": 0,  # Not in general insurance
                        "city": row.get('City', 'Unknown'),
                        "territory": row.get('Territory', 'Unknown'),
                        "industry": row.get('Industry', 'Unknown'),
                        "sector": row.get('Sector', 'Unknown'),
                        "num_employees": self._parse_int(row.get('Num of Employees', 0)),
                        "employee_size_tier": row.get('Employee Size Tier', ''),
                        "revenue": self._parse_float(row.get('Revenue', 0)),
                        "new_renewal": row.get('New or Renewal', 'New'),
                        "generation_date": datetime.utcnow(),
                        "last_updated": datetime.utcnow(),
                        "policy_in_force": True,
                        "policy_expiring": False
                    }

                    if policy["policy_number"]:
                        policies.append(policy)

                except Exception as e:
                    print(f"Error parsing row {i}: {e}")
                    continue

        print(f"Parsed {len(policies)} policies from {csv_path}")
        return policies

    def _parse_date(self, date_str: str) -> datetime:
        """Parse date string to datetime"""
        if not date_str or date_str.strip() == '':
            return datetime.utcnow()

        try:
            # Try different date formats
            for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%Y/%m/%d']:
                try:
                    return datetime.strptime(date_str.strip(), fmt)
                except:
                    continue
            return datetime.utcnow()
        except:
            return datetime.utcnow()

    def _parse_float(self, value: Any) -> float:
        """Parse float value"""
        try:
            if isinstance(value, str):
                value = value.replace('$', '').replace(',', '').strip()
            return float(value) if value else 0.0
        except:
            return 0.0

    def _parse_int(self, value: Any) -> int:
        """Parse integer value"""
        try:
            if isinstance(value, str):
                value = value.replace(',', '').strip()
            return int(float(value)) if value else 0
        except:
            return 0

    def generate_realistic_claims(self, policies: List[Dict[str, Any]], claim_ratio: float = 0.15) -> List[Dict[str, Any]]:
        """Generate realistic claims based on policies"""
        print(f"Generating claims for {len(policies)} policies...")
        claims = []

        # Select random policies to have claims
        policies_with_claims = secure_random.sample(policies, min(len(policies), int(len(policies) * claim_ratio)))

        claim_types = ["Collision", "Comprehensive", "Liability", "Property Damage", "Bodily Injury", "Theft", "Vandalism", "Fire", "Weather Damage"]

        for policy in policies_with_claims:
            num_claims = secure_random.choices([1, 2, 3], weights=[0.7, 0.2, 0.1])[0]

            for _ in range(num_claims):
                claim_id = f"CLM-{datetime.now().strftime('%Y%m')}-{secure_random.randint(10000, 99999)}"

                # Generate incident date within policy period
                policy_start = policy.get('policy_effective_date', datetime.utcnow())
                incident_date = policy_start + timedelta(days=secure_random.randint(0, 365))

                # Determine claim amount based on line of business
                lob = policy.get('line_of_business', '')
                if 'Auto' in lob:
                    base_amount = secure_random.uniform(1000, 50000)
                elif 'Workers' in lob:
                    base_amount = secure_random.uniform(5000, 100000)
                else:
                    base_amount = secure_random.uniform(2000, 75000)

                # Add some high-value outliers
                if secure_random.random() < 0.05:
                    base_amount *= secure_random.uniform(3, 10)

                claim_amount = round(base_amount, 2)

                # Generate fraud score (most are low, some are suspicious)
                if secure_random.random() < 0.85:
                    fraud_score = secure_random.uniform(0.0, 0.4)  # Low risk
                elif secure_random.random() < 0.90:
                    fraud_score = secure_random.uniform(0.4, 0.7)  # Medium risk
                else:
                    fraud_score = secure_random.uniform(0.7, 0.95)  # High risk

                claim = {
                    "claim_id": claim_id,
                    "policy_number": policy['policy_number'],
                    "customer_name": policy['primary_insured_customer_id'],
                    "customer_email": f"{policy['primary_insured_customer_id'].lower().replace(' ', '.')}@example.com",
                    "claim_type": secure_random.choice(claim_types),
                    "incident_date": incident_date,
                    "reported_date": incident_date + timedelta(days=secure_random.randint(0, 7)),
                    "claim_amount": claim_amount,
                    "description": self._generate_claim_description(secure_random.choice(claim_types)),
                    "location": {
                        "city": policy.get('city', 'Unknown'),
                        "state": policy.get('issue_state', 'CA')
                    },
                    "status": secure_random.choice(["submitted", "submitted", "submitted", "processing", "approved"]),
                    "current_stage": "initial_review",
                    "ai_recommendation": {
                        "fraud_score": fraud_score,
                        "policy_valid": True,
                        "recommended_action": "approve" if fraud_score < 0.6 else "investigate"
                    },
                    "fraud_score": fraud_score,
                    "priority": "urgent" if fraud_score > 0.7 or claim_amount > 75000 else "high" if fraud_score > 0.5 or claim_amount > 40000 else "normal",
                    "created_at": incident_date + timedelta(days=secure_random.randint(0, 7)),
                    "updated_at": datetime.utcnow(),
                    "last_updated": datetime.utcnow()
                }

                claims.append(claim)

        print(f"Generated {len(claims)} claims")
        return claims

    def _generate_claim_description(self, claim_type: str) -> str:
        """Generate realistic claim descriptions"""
        descriptions = {
            "Collision": [
                "Vehicle was rear-ended at a traffic light while stopped.",
                "Two-vehicle collision at intersection, other driver ran red light.",
                "Single-vehicle accident, lost control on wet road and hit guardrail.",
                "Parking lot collision, other vehicle backed into my car."
            ],
            "Comprehensive": [
                "Tree branch fell on vehicle during storm, significant roof damage.",
                "Windshield shattered from falling debris on highway.",
                "Hail damage to vehicle during severe weather event.",
                "Vehicle damaged by flood waters during heavy rain."
            ],
            "Theft": [
                "Vehicle stolen from parking garage overnight.",
                "Catalytic converter stolen from vehicle.",
                "Personal items stolen from locked vehicle.",
                "Vehicle broken into, electronics stolen."
            ],
            "Liability": [
                "Caused minor fender bender, rear-ended vehicle ahead.",
                "Backing accident in parking lot, hit another vehicle.",
                "Merged into lane and made contact with another vehicle.",
                "Failed to yield and caused collision."
            ],
            "Property Damage": [
                "Backed into garage door, significant damage to door.",
                "Hit mailbox while parking, property owner requesting compensation.",
                "Vehicle rolled into fence causing structural damage.",
                "Damage to commercial property during parking."
            ]
        }

        desc_list = descriptions.get(claim_type, ["Claim incident occurred requiring insurance coverage."])
        return secure_random.choice(desc_list)

    async def load_policies(self, policies: List[Dict[str, Any]]):
        """Load policies into MongoDB"""
        if not policies:
            print("No policies to load")
            return

        print(f"Loading {len(policies)} policies into MongoDB...")

        # Insert policies (ignore duplicates)
        try:
            result = await self.db.policies.insert_many(policies, ordered=False)
            print(f"Inserted {len(result.inserted_ids)} policies")
        except Exception as e:
            print(f"Some policies may already exist: {e}")

        # Create indexes
        await self.db.policies.create_index("policy_number", unique=True)
        print("Policy indexes created")

    async def load_claims(self, claims: List[Dict[str, Any]]):
        """Load claims into MongoDB"""
        if not claims:
            print("No claims to load")
            return

        print(f"Loading {len(claims)} claims into MongoDB...")

        # Insert claims (ignore duplicates)
        try:
            result = await self.db.claims.insert_many(claims, ordered=False)
            print(f"Inserted {len(result.inserted_ids)} claims")
        except Exception as e:
            print(f"Some claims may already exist: {e}")

        # Create indexes
        await self.db.claims.create_index("claim_id", unique=True)
        await self.db.claims.create_index("policy_number")
        await self.db.claims.create_index("status")
        print("Claim indexes created")

    async def load_from_zip(self, zip_path: str, policy_limit: int = 500):
        """Main method to load data from zip file"""
        print(f"\n{'='*60}")
        print("SYNTHETIC INSURANCE DATA LOADER")
        print(f"{'='*60}\n")

        # Extract zip
        csv_files = self.extract_zip_file(zip_path)

        if not csv_files:
            print("No CSV files found in zip!")
            return

        # Connect to MongoDB
        await self.connect()

        # Parse policies from CSV
        all_policies = []
        for csv_file in csv_files[:1]:  # Use first CSV file for demo
            policies = self.parse_policy_csv(csv_file, limit=policy_limit)
            all_policies.extend(policies)

        # Load policies
        await self.load_policies(all_policies)

        # Generate and load claims
        claims = self.generate_realistic_claims(all_policies, claim_ratio=0.18)
        await self.load_claims(claims)

        # Disconnect
        await self.disconnect()

        print(f"\n{'='*60}")
        print("DATA LOADING COMPLETE")
        print(f"Policies loaded: {len(all_policies)}")
        print(f"Claims generated: {len(claims)}")
        print(f"{'='*60}\n")


async def main():
    """Main entry point"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python data_loader.py <path_to_synthetic_data.zip>")
        print("\nExample:")
        print("  python data_loader.py newdata/syntheticdatageneral/dist/SyntheticInsuranceData-byPolicy-2022-08-11.zip")
        sys.exit(1)

    zip_path = sys.argv[1]

    if not os.path.exists(zip_path):
        print(f"Error: File not found: {zip_path}")
        sys.exit(1)

    loader = SyntheticDataLoader()
    await loader.load_from_zip(zip_path, policy_limit=500)


if __name__ == "__main__":
    asyncio.run(main())
