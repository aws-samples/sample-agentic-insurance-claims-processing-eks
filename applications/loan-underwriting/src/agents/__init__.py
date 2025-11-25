"""
AI Agents for Loan Underwriting

This package contains specialized agents for different aspects of loan underwriting:
- Coordinator Agent: Orchestrates the multi-agent workflow
- Credit Analysis Agent: Evaluates creditworthiness
- Income Verification Agent: Verifies employment and income
- Risk Assessment Agent: Assesses loan default risk
- Compliance Agent: Ensures regulatory compliance
"""

from .coordinator_agent import CoordinatorAgent

__all__ = ["CoordinatorAgent"]
