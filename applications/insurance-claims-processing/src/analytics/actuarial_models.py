"""
Actuarial Models and Predictive Analytics
Advanced statistical models for claims prediction, loss reserving, and risk assessment
"""

import numpy as np
import pandas as pd
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import joblib
import json

# Machine Learning imports
from sklearn.ensemble import RandomForestRegressor, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, mean_squared_error, classification_report

# Statistical analysis
from scipy import stats
from scipy.optimize import minimize
import statsmodels.api as sm

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModelType(str, Enum):
    LOSS_RESERVING = "loss_reserving"
    FRAUD_DETECTION = "fraud_detection"
    CLAIM_SEVERITY = "claim_severity"
    CLAIM_FREQUENCY = "claim_frequency"
    SETTLEMENT_PREDICTION = "settlement_prediction"
    LITIGATION_RISK = "litigation_risk"
    SUBROGATION_POTENTIAL = "subrogation_potential"

@dataclass
class ActuarialPrediction:
    """Result from actuarial model prediction"""
    model_type: ModelType
    prediction: float
    confidence_interval: Tuple[float, float]
    probability: Optional[float] = None
    risk_factors: List[str] = None
    model_version: str = "1.0"
    prediction_date: str = None

    def __post_init__(self):
        if self.prediction_date is None:
            self.prediction_date = datetime.utcnow().isoformat()

@dataclass
class LossReserveAnalysis:
    """Comprehensive loss reserve analysis"""
    claim_id: str
    case_reserve: float
    ibnr_reserve: float  # Incurred But Not Reported
    alae_reserve: float  # Allocated Loss Adjustment Expenses
    total_reserve: float

    # Development patterns
    development_factors: List[float]
    expected_ultimate: float
    reserve_adequacy: float  # Percentage adequate

    # Confidence metrics
    coefficient_of_variation: float
    confidence_level: float

    # Explanatory factors
    key_variables: Dict[str, float]
    methodology: str

class ChainLadderModel:
    """Chain Ladder method for loss reserving"""

    def __init__(self):
        self.development_factors = None
        self.tail_factor = 1.0
        self.is_fitted = False

    def fit(self, loss_triangle: pd.DataFrame) -> None:
        """Fit chain ladder model to loss triangle data"""
        try:
            # Calculate age-to-age development factors
            factors = []

            for i in range(loss_triangle.shape[1] - 1):
                current_col = loss_triangle.iloc[:, i]
                next_col = loss_triangle.iloc[:, i + 1]

                # Remove zeros and calculate ratios
                valid_ratios = next_col[current_col > 0] / current_col[current_col > 0]
                valid_ratios = valid_ratios[np.isfinite(valid_ratios)]

                if len(valid_ratios) > 0:
                    # Use volume-weighted average
                    weights = current_col[current_col > 0]
                    factor = np.average(valid_ratios, weights=weights)
                    factors.append(factor)
                else:
                    factors.append(1.0)

            self.development_factors = np.array(factors)

            # Estimate tail factor (simple approach)
            if len(factors) > 2:
                self.tail_factor = max(1.0, np.mean(factors[-2:]))

            self.is_fitted = True
            logger.info("Chain Ladder model fitted successfully")

        except Exception as e:
            logger.error(f"Error fitting Chain Ladder model: {e}")
            raise

    def predict_ultimate(self,
                        accident_year: int,
                        current_cumulative: float,
                        development_period: int) -> float:
        """Predict ultimate loss for given accident year"""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction")

        # Apply remaining development factors
        ultimate = current_cumulative

        for i in range(development_period, len(self.development_factors)):
            ultimate *= self.development_factors[i]

        # Apply tail factor
        ultimate *= self.tail_factor

        return ultimate

class BornhuetterFergusonModel:
    """Bornhuetter-Ferguson method for loss reserving"""

    def __init__(self):
        self.expected_loss_ratios = {}
        self.development_factors = None
        self.is_fitted = False

    def fit(self,
            loss_triangle: pd.DataFrame,
            premium_data: Dict[int, float],
            expected_loss_ratios: Dict[int, float]) -> None:
        """Fit BF model"""
        try:
            self.expected_loss_ratios = expected_loss_ratios

            # Calculate development factors (similar to Chain Ladder)
            factors = []
            for i in range(loss_triangle.shape[1] - 1):
                current_col = loss_triangle.iloc[:, i]
                next_col = loss_triangle.iloc[:, i + 1]

                valid_ratios = next_col[current_col > 0] / current_col[current_col > 0]
                valid_ratios = valid_ratios[np.isfinite(valid_ratios)]

                if len(valid_ratios) > 0:
                    factor = np.mean(valid_ratios)
                    factors.append(factor)
                else:
                    factors.append(1.0)

            self.development_factors = np.array(factors)
            self.is_fitted = True

        except Exception as e:
            logger.error(f"Error fitting BF model: {e}")
            raise

    def predict_ultimate(self,
                        accident_year: int,
                        current_cumulative: float,
                        premium: float,
                        development_period: int) -> float:
        """Predict ultimate using BF method"""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction")

        # Expected ultimate based on loss ratio
        expected_ultimate = premium * self.expected_loss_ratios.get(accident_year, 0.65)

        # Calculate percent reported to date
        cumulative_development = 1.0
        for i in range(development_period):
            if i < len(self.development_factors):
                cumulative_development *= self.development_factors[i]

        percent_reported = 1.0 / cumulative_development if cumulative_development > 0 else 1.0
        percent_reported = min(1.0, percent_reported)

        # BF formula
        unreported_expected = expected_ultimate * (1 - percent_reported)
        ultimate = current_cumulative + unreported_expected

        return ultimate

class FraudDetectionModel:
    """Advanced ML model for fraud detection"""

    def __init__(self):
        self.model = GradientBoostingClassifier(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=6,
            random_state=42
        )
        self.scaler = StandardScaler()
        self.feature_columns = None
        self.is_fitted = False

    def prepare_features(self, claim_data: Dict[str, Any]) -> np.array:
        """Prepare features for fraud detection"""
        features = []

        # Claim amount features
        claim_amount = float(claim_data.get('claim_amount', 0))
        features.extend([
            claim_amount,
            np.log1p(claim_amount),  # Log transform
            1 if claim_amount > 50000 else 0,  # High amount flag
            1 if claim_amount % 1000 == 0 else 0  # Round number flag
        ])

        # Time-based features
        incident_date = pd.to_datetime(claim_data.get('incident_date', datetime.now()))
        report_date = pd.to_datetime(claim_data.get('reported_date', datetime.now()))

        reporting_delay = (report_date - incident_date).days
        features.extend([
            reporting_delay,
            1 if reporting_delay > 30 else 0,  # Late reporting
            incident_date.weekday(),  # Day of week
            incident_date.hour if hasattr(incident_date, 'hour') else 12  # Hour
        ])

        # Policy features
        policy_age_days = (datetime.now() - pd.to_datetime(claim_data.get('policy_effective_date', datetime.now()))).days
        features.extend([
            policy_age_days,
            1 if policy_age_days < 90 else 0,  # New policy flag
        ])

        # Vehicle features (if applicable)
        vehicle_age = datetime.now().year - int(claim_data.get('vehicle_year', datetime.now().year))
        features.extend([
            vehicle_age,
            1 if vehicle_age > 10 else 0  # Old vehicle flag
        ])

        # External data features
        weather_data = claim_data.get('weather_data', {})
        features.extend([
            float(weather_data.get('precipitation', 0)),
            float(weather_data.get('wind_speed', 0)),
            1 if weather_data.get('severe_weather', False) else 0
        ])

        # Historical features
        previous_claims = int(claim_data.get('previous_claims_count', 0))
        features.extend([
            previous_claims,
            1 if previous_claims > 2 else 0  # Frequent claimant
        ])

        return np.array(features).reshape(1, -1)

    def fit(self, training_data: List[Dict[str, Any]], labels: List[int]) -> None:
        """Train fraud detection model"""
        try:
            # Prepare training features
            X_train = []
            for claim in training_data:
                features = self.prepare_features(claim).flatten()
                X_train.append(features)

            X_train = np.array(X_train)
            y_train = np.array(labels)

            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)

            # Train model
            self.model.fit(X_train_scaled, y_train)

            # Store feature column count for consistency
            self.feature_columns = X_train.shape[1]
            self.is_fitted = True

            # Log performance
            train_score = self.model.score(X_train_scaled, y_train)
            logger.info(f"Fraud model trained. Training accuracy: {train_score:.3f}")

        except Exception as e:
            logger.error(f"Error training fraud model: {e}")
            raise

    def predict_fraud_probability(self, claim_data: Dict[str, Any]) -> float:
        """Predict fraud probability for a claim"""
        if not self.is_fitted:
            # Return baseline estimate if model not trained
            logger.warning("Fraud model not trained, using baseline estimation")
            return self._baseline_fraud_estimate(claim_data)

        try:
            features = self.prepare_features(claim_data)

            # Ensure feature consistency
            if features.shape[1] != self.feature_columns:
                logger.warning(f"Feature mismatch: expected {self.feature_columns}, got {features.shape[1]}")
                return self._baseline_fraud_estimate(claim_data)

            features_scaled = self.scaler.transform(features)
            fraud_probability = self.model.predict_proba(features_scaled)[0, 1]

            return float(fraud_probability)

        except Exception as e:
            logger.error(f"Error predicting fraud probability: {e}")
            return self._baseline_fraud_estimate(claim_data)

    def _baseline_fraud_estimate(self, claim_data: Dict[str, Any]) -> float:
        """Baseline fraud estimate using simple rules"""
        score = 0.0

        # High amount
        if claim_data.get('claim_amount', 0) > 50000:
            score += 0.3

        # Late reporting
        incident_date = pd.to_datetime(claim_data.get('incident_date', datetime.now()))
        report_date = pd.to_datetime(claim_data.get('reported_date', datetime.now()))
        if (report_date - incident_date).days > 30:
            score += 0.2

        # New policy
        policy_effective = pd.to_datetime(claim_data.get('policy_effective_date', datetime.now()))
        if (datetime.now() - policy_effective).days < 90:
            score += 0.2

        # Multiple previous claims
        if claim_data.get('previous_claims_count', 0) > 2:
            score += 0.3

        return min(1.0, score)

class ClaimSeverityModel:
    """Model to predict claim severity/ultimate cost"""

    def __init__(self):
        self.model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        self.scaler = StandardScaler()
        self.log_transform = True
        self.is_fitted = False

    def prepare_features(self, claim_data: Dict[str, Any]) -> np.array:
        """Prepare features for severity prediction"""
        features = []

        # Claim characteristics
        features.extend([
            float(claim_data.get('policy_limit', 100000)),
            float(claim_data.get('deductible', 1000)),
            1 if claim_data.get('claim_type') == 'collision' else 0,
            1 if claim_data.get('claim_type') == 'comprehensive' else 0,
            1 if claim_data.get('claim_type') == 'liability' else 0
        ])

        # Vehicle characteristics
        vehicle_age = datetime.now().year - int(claim_data.get('vehicle_year', datetime.now().year))
        features.extend([
            vehicle_age,
            float(claim_data.get('vehicle_value', 20000)),
            1 if claim_data.get('vehicle_make', '').lower() in ['bmw', 'mercedes', 'audi', 'lexus'] else 0  # Luxury flag
        ])

        # Geographic features
        features.extend([
            1 if claim_data.get('jurisdiction', '').upper() in ['CA', 'NY', 'FL'] else 0,  # High cost states
            float(claim_data.get('area_cost_index', 1.0))  # Cost of living index
        ])

        # Incident characteristics
        features.extend([
            1 if claim_data.get('injury_involved', False) else 0,
            int(claim_data.get('num_vehicles_involved', 1)),
            1 if claim_data.get('towed', False) else 0
        ])

        # Weather at time of incident
        weather_data = claim_data.get('weather_data', {})
        features.extend([
            1 if weather_data.get('severe_weather', False) else 0,
            float(weather_data.get('visibility', 10))
        ])

        return np.array(features).reshape(1, -1)

    def fit(self, training_data: List[Dict[str, Any]], ultimate_costs: List[float]) -> None:
        """Train severity prediction model"""
        try:
            # Prepare features
            X_train = []
            for claim in training_data:
                features = self.prepare_features(claim).flatten()
                X_train.append(features)

            X_train = np.array(X_train)
            y_train = np.array(ultimate_costs)

            # Log transform target if beneficial
            if self.log_transform:
                y_train = np.log1p(y_train)

            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)

            # Train model
            self.model.fit(X_train_scaled, y_train)
            self.is_fitted = True

            # Log performance
            train_score = self.model.score(X_train_scaled, y_train)
            logger.info(f"Severity model trained. Training R²: {train_score:.3f}")

        except Exception as e:
            logger.error(f"Error training severity model: {e}")
            raise

    def predict_ultimate_cost(self, claim_data: Dict[str, Any]) -> Tuple[float, Tuple[float, float]]:
        """Predict ultimate claim cost with confidence interval"""
        if not self.is_fitted:
            return self._baseline_severity_estimate(claim_data)

        try:
            features = self.prepare_features(claim_data)
            features_scaled = self.scaler.transform(features)

            # Get prediction from all trees for confidence interval
            tree_predictions = []
            for tree in self.model.estimators_:
                pred = tree.predict(features_scaled)[0]
                tree_predictions.append(pred)

            mean_pred = np.mean(tree_predictions)
            std_pred = np.std(tree_predictions)

            # Convert back from log space if needed
            if self.log_transform:
                mean_pred = np.expm1(mean_pred)
                # Approximate confidence interval transformation
                lower_ci = np.expm1(mean_pred - 1.96 * std_pred)
                upper_ci = np.expm1(mean_pred + 1.96 * std_pred)
            else:
                lower_ci = mean_pred - 1.96 * std_pred
                upper_ci = mean_pred + 1.96 * std_pred

            confidence_interval = (max(0, lower_ci), upper_ci)

            return float(mean_pred), confidence_interval

        except Exception as e:
            logger.error(f"Error predicting severity: {e}")
            return self._baseline_severity_estimate(claim_data)

    def _baseline_severity_estimate(self, claim_data: Dict[str, Any]) -> Tuple[float, Tuple[float, float]]:
        """Baseline severity estimate"""
        # Simple baseline based on claim type and vehicle value
        base_cost = 5000  # Default

        claim_type = claim_data.get('claim_type', '').lower()
        if claim_type == 'collision':
            base_cost = 8000
        elif claim_type == 'comprehensive':
            base_cost = 4000
        elif claim_type == 'liability':
            base_cost = 15000

        # Adjust for vehicle value
        vehicle_value = float(claim_data.get('vehicle_value', 20000))
        if vehicle_value > 50000:
            base_cost *= 1.5
        elif vehicle_value < 10000:
            base_cost *= 0.7

        # Simple confidence interval
        confidence_interval = (base_cost * 0.5, base_cost * 2.0)

        return base_cost, confidence_interval

class ActuarialAnalyticsEngine:
    """Main engine coordinating all actuarial models"""

    def __init__(self):
        self.models = {
            ModelType.FRAUD_DETECTION: FraudDetectionModel(),
            ModelType.CLAIM_SEVERITY: ClaimSeverityModel(),
            ModelType.LOSS_RESERVING: ChainLadderModel()
        }

        self.model_metadata = {}
        self.performance_history = {}

    async def comprehensive_claim_analysis(self, claim_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive actuarial analysis of a claim"""
        results = {}

        try:
            # Fraud detection
            fraud_model = self.models[ModelType.FRAUD_DETECTION]
            fraud_probability = fraud_model.predict_fraud_probability(claim_data)

            results['fraud_analysis'] = ActuarialPrediction(
                model_type=ModelType.FRAUD_DETECTION,
                prediction=fraud_probability,
                probability=fraud_probability,
                confidence_interval=(max(0, fraud_probability - 0.1), min(1, fraud_probability + 0.1)),
                risk_factors=self._identify_fraud_risk_factors(claim_data, fraud_probability)
            )

            # Severity prediction
            severity_model = self.models[ModelType.CLAIM_SEVERITY]
            predicted_cost, cost_ci = severity_model.predict_ultimate_cost(claim_data)

            results['severity_analysis'] = ActuarialPrediction(
                model_type=ModelType.CLAIM_SEVERITY,
                prediction=predicted_cost,
                confidence_interval=cost_ci,
                risk_factors=self._identify_severity_risk_factors(claim_data)
            )

            # Loss reserving (if enough data)
            if 'accident_year' in claim_data and 'development_period' in claim_data:
                results['reserve_analysis'] = await self._perform_reserve_analysis(claim_data)

            # Overall risk assessment
            results['overall_risk'] = self._calculate_overall_risk(results)

            logger.info(f"Comprehensive analysis completed for claim {claim_data.get('claim_id')}")

        except Exception as e:
            logger.error(f"Error in comprehensive analysis: {e}")
            results['error'] = str(e)

        return results

    def _identify_fraud_risk_factors(self, claim_data: Dict[str, Any], fraud_score: float) -> List[str]:
        """Identify key fraud risk factors"""
        risk_factors = []

        if fraud_score > 0.7:
            # High amount
            if claim_data.get('claim_amount', 0) > 50000:
                risk_factors.append("High claim amount")

            # Late reporting
            incident_date = pd.to_datetime(claim_data.get('incident_date', datetime.now()))
            report_date = pd.to_datetime(claim_data.get('reported_date', datetime.now()))
            if (report_date - incident_date).days > 30:
                risk_factors.append("Late claim reporting")

            # New policy
            policy_effective = pd.to_datetime(claim_data.get('policy_effective_date', datetime.now()))
            if (datetime.now() - policy_effective).days < 90:
                risk_factors.append("New policy (less than 90 days)")

            # Previous claims
            if claim_data.get('previous_claims_count', 0) > 2:
                risk_factors.append("Multiple previous claims")

            # Round dollar amounts
            if claim_data.get('claim_amount', 0) % 1000 == 0:
                risk_factors.append("Round dollar amount")

        return risk_factors

    def _identify_severity_risk_factors(self, claim_data: Dict[str, Any]) -> List[str]:
        """Identify factors that increase claim severity"""
        risk_factors = []

        if claim_data.get('injury_involved', False):
            risk_factors.append("Bodily injury involved")

        if claim_data.get('num_vehicles_involved', 1) > 2:
            risk_factors.append("Multi-vehicle incident")

        if claim_data.get('vehicle_year', datetime.now().year) < datetime.now().year - 10:
            risk_factors.append("Older vehicle (higher repair complexity)")

        if claim_data.get('jurisdiction', '').upper() in ['CA', 'NY', 'FL']:
            risk_factors.append("High-cost jurisdiction")

        weather_data = claim_data.get('weather_data', {})
        if weather_data.get('severe_weather', False):
            risk_factors.append("Severe weather conditions")

        return risk_factors

    async def _perform_reserve_analysis(self, claim_data: Dict[str, Any]) -> LossReserveAnalysis:
        """
        Perform loss reserve analysis for a claim.

        NOTE: This implementation uses simplified fixed percentages for demonstration purposes.
        In a production environment, reserves should be calculated using:

        1. Case Reserve: Adjuster's estimate based on claim investigation, not a fixed percentage.
           Should reflect the expected cost to settle the specific claim.

        2. IBNR (Incurred But Not Reported): Calculated at portfolio level using actuarial methods:
           - Chain Ladder / Development Triangle method
           - Bornhuetter-Ferguson method
           - Expected Loss Ratio method
           IBNR is NOT calculated per-claim; it's a bulk reserve for unreported claims.

        3. ALAE (Allocated Loss Adjustment Expenses): Actual or estimated costs for:
           - Legal fees, expert witnesses, independent adjusters
           - Should be tracked per-claim or estimated using historical LAE-to-loss ratios

        Industry Context:
        - Total Reserves = Case Reserves + IBNR + ALAE + ULAE (Unallocated LAE)
        - Reserve adequacy is typically reviewed quarterly by actuaries
        - Regulatory requirements (e.g., SAP, GAAP) dictate reserve calculation standards

        The fixed percentages below (80%, 20%, 15%) are SIMPLIFIED PLACEHOLDERS
        and do not represent actuarially sound reserve estimates.
        """
        claim_amount = float(claim_data.get('claim_amount', 0))
        accident_year = int(claim_data.get('accident_year', datetime.now().year))
        development_period = int(claim_data.get('development_period', 1))

        # SIMPLIFIED reserve estimation for demonstration
        # Production systems should use actuarial triangles and claim-specific analysis
        case_reserve = claim_amount * 0.8   # Placeholder: 80% of reported amount
        ibnr_reserve = claim_amount * 0.2   # Placeholder: 20% IBNR (should be portfolio-level)
        alae_reserve = claim_amount * 0.15  # Placeholder: 15% ALAE (should be claim-specific or historical ratio)

        total_reserve = case_reserve + ibnr_reserve + alae_reserve

        return LossReserveAnalysis(
            claim_id=claim_data.get('claim_id', 'unknown'),
            case_reserve=case_reserve,
            ibnr_reserve=ibnr_reserve,
            alae_reserve=alae_reserve,
            total_reserve=total_reserve,
            development_factors=[1.2, 1.1, 1.05, 1.02, 1.01],  # Typical factors
            expected_ultimate=claim_amount * 1.25,
            reserve_adequacy=0.85,
            coefficient_of_variation=0.15,
            confidence_level=0.75,
            key_variables={
                'claim_amount': claim_amount,
                'development_period': development_period,
                'accident_year': accident_year
            },
            methodology="simplified_chain_ladder"
        )

    def _calculate_overall_risk(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall risk assessment"""
        fraud_score = analysis_results.get('fraud_analysis', {}).prediction or 0
        severity_prediction = analysis_results.get('severity_analysis', {}).prediction or 0

        # Combine fraud and severity for overall risk
        risk_score = (fraud_score * 0.4) + min(1.0, severity_prediction / 100000 * 0.6)

        risk_level = "low"
        if risk_score > 0.7:
            risk_level = "high"
        elif risk_score > 0.4:
            risk_level = "medium"

        return {
            "overall_risk_score": risk_score,
            "risk_level": risk_level,
            "recommendation": self._get_risk_recommendation(risk_level, fraud_score, severity_prediction)
        }

    def _get_risk_recommendation(self, risk_level: str, fraud_score: float, severity: float) -> str:
        """Get recommendation based on risk assessment"""
        if risk_level == "high":
            if fraud_score > 0.7:
                return "SIU investigation required - high fraud probability"
            elif severity > 50000:
                return "Senior adjuster assignment - high severity expected"
            else:
                return "Enhanced investigation recommended"
        elif risk_level == "medium":
            return "Standard investigation with close monitoring"
        else:
            return "Standard processing appropriate"

# Global analytics engine
actuarial_engine = ActuarialAnalyticsEngine()

# Factory functions for model training
async def train_fraud_model_from_data(training_file_path: str):
    """Train fraud model from historical data"""
    try:
        # Load training data (would be from database in production)
        training_data = pd.read_csv(training_file_path)

        claims = training_data.to_dict('records')
        labels = training_data['is_fraud'].tolist()

        fraud_model = actuarial_engine.models[ModelType.FRAUD_DETECTION]
        fraud_model.fit(claims, labels)

        logger.info("Fraud model training completed")

    except Exception as e:
        logger.error(f"Error training fraud model: {e}")

async def train_severity_model_from_data(training_file_path: str):
    """Train severity model from historical data"""
    try:
        training_data = pd.read_csv(training_file_path)

        claims = training_data.to_dict('records')
        ultimate_costs = training_data['ultimate_cost'].tolist()

        severity_model = actuarial_engine.models[ModelType.CLAIM_SEVERITY]
        severity_model.fit(claims, ultimate_costs)

        logger.info("Severity model training completed")

    except Exception as e:
        logger.error(f"Error training severity model: {e}")

# Model persistence
def save_models(models_directory: str):
    """Save trained models to disk"""
    import os
    os.makedirs(models_directory, exist_ok=True)

    for model_type, model in actuarial_engine.models.items():
        if hasattr(model, 'is_fitted') and model.is_fitted:
            model_path = os.path.join(models_directory, f"{model_type.value}_model.joblib")
            joblib.dump(model, model_path)
            logger.info(f"Saved {model_type.value} model")

def load_models(models_directory: str):
    """Load trained models from disk"""
    import os

    for model_type in ModelType:
        model_path = os.path.join(models_directory, f"{model_type.value}_model.joblib")
        if os.path.exists(model_path):
            try:
                actuarial_engine.models[model_type] = joblib.load(model_path)
                logger.info(f"Loaded {model_type.value} model")
            except Exception as e:
                logger.error(f"Error loading {model_type.value} model: {e}")