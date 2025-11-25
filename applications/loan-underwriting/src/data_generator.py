"""
Sample Loan Application Data Generator
Creates realistic loan applications for testing the underwriting system
"""

import random
import json
from datetime import datetime, timedelta
from typing import List, Dict
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database_models import (
    LoanApplication, LoanType, LoanStatus, EmploymentType,
    Address, Employment, FinancialInformation, LoanDetails
)


class LoanDataGenerator:
    """Generate realistic loan application data"""

    def __init__(self):
        self.first_names = [
            "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda",
            "William", "Barbara", "David", "Elizabeth", "Richard", "Susan", "Joseph", "Jessica",
            "Thomas", "Sarah", "Charles", "Karen", "Christopher", "Nancy", "Daniel", "Lisa"
        ]

        self.last_names = [
            "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
            "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
            "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Thompson", "White"
        ]

        self.cities = [
            ("Seattle", "WA", "98101"),
            ("Portland", "OR", "97201"),
            ("San Francisco", "CA", "94102"),
            ("Los Angeles", "CA", "90001"),
            ("San Diego", "CA", "92101"),
            ("Phoenix", "AZ", "85001"),
            ("Denver", "CO", "80201"),
            ("Austin", "TX", "78701"),
            ("Dallas", "TX", "75201"),
            ("Houston", "TX", "77001"),
            ("Chicago", "IL", "60601"),
            ("New York", "NY", "10001"),
            ("Boston", "MA", "02101"),
            ("Miami", "FL", "33101"),
            ("Atlanta", "GA", "30301")
        ]

        self.employers = [
            "Amazon", "Microsoft", "Google", "Apple", "Meta", "Tesla", "Boeing",
            "Starbucks", "Costco", "Target", "Walmart", "Home Depot", "Wells Fargo",
            "Bank of America", "JPMorgan Chase", "UPS", "FedEx", "Acme Corp",
            "Tech Solutions Inc", "Healthcare Plus", "Education First", "Construction Co"
        ]

        self.job_titles = [
            "Software Engineer", "Product Manager", "Data Analyst", "Sales Manager",
            "Marketing Director", "Operations Manager", "Project Manager", "Accountant",
            "HR Manager", "Teacher", "Nurse", "Mechanic", "Electrician", "Plumber",
            "Construction Manager", "Restaurant Manager", "Store Manager", "Consultant"
        ]

        self.loan_purposes = {
            LoanType.PERSONAL: [
                "Debt consolidation",
                "Home improvement",
                "Medical expenses",
                "Wedding expenses",
                "Vacation",
                "Emergency expenses"
            ],
            LoanType.AUTO: [
                "Purchase new vehicle",
                "Purchase used vehicle",
                "Refinance existing auto loan"
            ],
            LoanType.MORTGAGE: [
                "Purchase primary residence",
                "Purchase investment property",
                "Refinance existing mortgage"
            ],
            LoanType.BUSINESS: [
                "Start new business",
                "Expand existing business",
                "Purchase equipment",
                "Working capital"
            ],
            LoanType.HOME_EQUITY: [
                "Home renovation",
                "Debt consolidation",
                "Education expenses",
                "Investment opportunity"
            ]
        }

    def generate_application(self, loan_type: LoanType = None) -> Dict:
        """Generate a single random loan application"""

        if loan_type is None:
            loan_type = random.choice(list(LoanType))

        first_name = random.choice(self.first_names)
        last_name = random.choice(self.last_names)
        city, state, zip_code = random.choice(self.cities)

        # Generate realistic age (21-65)
        age = random.randint(21, 65)
        dob = datetime.now() - timedelta(days=age * 365 + random.randint(0, 364))

        # Generate financial profile
        annual_income = self._generate_income()
        monthly_income = annual_income / 12
        monthly_debts = random.uniform(monthly_income * 0.1, monthly_income * 0.45)
        credit_score = self._generate_credit_score()

        # Generate employment
        years_employed = random.uniform(0.5, 20)
        employer = random.choice(self.employers)

        # Generate loan details based on type
        loan_details = self._generate_loan_details(loan_type, annual_income, credit_score)

        application = LoanApplication(
            borrower_first_name=first_name,
            borrower_last_name=last_name,
            borrower_email=f"{first_name.lower()}.{last_name.lower()}@email.com",
            borrower_phone=f"+1{random.randint(2000000000, 9999999999)}",
            date_of_birth=dob,
            ssn_last_4=f"{random.randint(0, 9999):04d}",
            current_address=Address(
                street=f"{random.randint(100, 9999)} {random.choice(['Main', 'Oak', 'Pine', 'Maple', 'Cedar'])} {random.choice(['St', 'Ave', 'Blvd', 'Dr'])}",
                city=city,
                state=state,
                zip_code=zip_code,
                residence_type=random.choice(["own", "rent"]),
                years_at_address=random.uniform(0.5, 20)
            ),
            employment=Employment(
                employer_name=employer,
                employment_type=random.choice([EmploymentType.FULL_TIME, EmploymentType.PART_TIME, EmploymentType.SELF_EMPLOYED]),
                job_title=random.choice(self.job_titles),
                years_employed=years_employed,
                monthly_income=monthly_income
            ),
            financial_info=FinancialInformation(
                annual_income=annual_income,
                monthly_income=monthly_income,
                other_income=random.uniform(0, monthly_income * 0.2) if random.random() > 0.7 else 0,
                monthly_debts=monthly_debts,
                credit_score=credit_score,
                assets={
                    "checking": random.uniform(1000, 50000),
                    "savings": random.uniform(5000, 200000),
                    "investments": random.uniform(0, 500000) if random.random() > 0.5 else 0
                },
                liabilities={
                    "credit_cards": random.uniform(0, 25000),
                    "student_loans": random.uniform(0, 100000) if random.random() > 0.6 else 0,
                    "auto_loans": random.uniform(0, 40000) if random.random() > 0.5 else 0
                }
            ),
            loan_details=loan_details,
            status=LoanStatus.SUBMITTED,
            submitted_at=datetime.utcnow()
        )

        return application.dict(by_alias=True, exclude={"id"})

    def _generate_income(self) -> float:
        """Generate realistic annual income"""
        # Distribution skewed towards median
        base = random.gauss(75000, 35000)
        return max(20000, min(500000, base))

    def _generate_credit_score(self) -> int:
        """Generate realistic credit score"""
        # Normal distribution around 700
        score = int(random.gauss(700, 80))
        return max(300, min(850, score))

    def _generate_loan_details(self, loan_type: LoanType, annual_income: float, credit_score: int) -> LoanDetails:
        """Generate loan details based on type and borrower profile"""

        purpose = random.choice(self.loan_purposes[loan_type])

        if loan_type == LoanType.PERSONAL:
            amount = random.uniform(1000, min(50000, annual_income * 0.3))
            term = random.choice([12, 24, 36, 48, 60])
            down_payment = 0

        elif loan_type == LoanType.AUTO:
            amount = random.uniform(10000, min(80000, annual_income * 0.5))
            term = random.choice([36, 48, 60, 72])
            down_payment = amount * random.uniform(0.1, 0.3)

        elif loan_type == LoanType.MORTGAGE:
            amount = random.uniform(150000, min(1000000, annual_income * 4))
            term = random.choice([180, 240, 300, 360])
            down_payment = amount * random.uniform(0.05, 0.25)

        elif loan_type == LoanType.BUSINESS:
            amount = random.uniform(25000, min(500000, annual_income * 2))
            term = random.choice([36, 60, 84, 120])
            down_payment = amount * random.uniform(0, 0.2)

        elif loan_type == LoanType.HOME_EQUITY:
            amount = random.uniform(10000, min(250000, annual_income * 0.8))
            term = random.choice([60, 120, 180, 240])
            down_payment = 0

        else:
            amount = 25000
            term = 60
            down_payment = 0

        return LoanDetails(
            loan_type=loan_type,
            requested_amount=round(amount, 2),
            loan_term_months=term,
            purpose=purpose,
            down_payment=round(down_payment, 2)
        )

    def generate_batch(self, count: int, loan_type: LoanType = None) -> List[Dict]:
        """Generate multiple loan applications"""
        return [self.generate_application(loan_type) for _ in range(count)]

    def save_to_file(self, applications: List[Dict], filename: str = "sample_loans.json"):
        """Save generated applications to JSON file"""
        with open(filename, 'w') as f:
            json.dump(applications, f, indent=2, default=str)
        print(f"Saved {len(applications)} applications to {filename}")


# ============================================================================
# CLI Interface
# ============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate sample loan applications")
    parser.add_argument("--count", type=int, default=10, help="Number of applications to generate")
    parser.add_argument("--type", choices=[lt.value for lt in LoanType], help="Specific loan type")
    parser.add_argument("--output", default="sample_loans.json", help="Output file name")

    args = parser.parse_args()

    generator = LoanDataGenerator()

    loan_type = LoanType(args.type) if args.type else None
    applications = generator.generate_batch(args.count, loan_type)

    # Print summary
    print(f"\nGenerated {len(applications)} loan applications:")
    type_counts = {}
    for app in applications:
        lt = app['loan_details']['loan_type']
        type_counts[lt] = type_counts.get(lt, 0) + 1

    for lt, count in type_counts.items():
        print(f"  - {lt}: {count}")

    # Save to file
    generator.save_to_file(applications, args.output)

    # Print sample
    print(f"\nSample application:")
    sample = applications[0]
    print(f"  Name: {sample['borrower_first_name']} {sample['borrower_last_name']}")
    print(f"  Income: ${sample['financial_info']['annual_income']:,.0f}/year")
    print(f"  Credit Score: {sample['financial_info']['credit_score']}")
    print(f"  Loan: {sample['loan_details']['loan_type']} - ${sample['loan_details']['requested_amount']:,.0f}")
