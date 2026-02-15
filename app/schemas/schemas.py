from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class DecisionType(str, Enum):
    RELOCATION = "relocation"
    PURCHASE = "purchase"
    JOB = "job"
    INVESTMENT = "investment"


class SimulationStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


# User schemas
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    created_at: datetime

    class Config:
        from_attributes = True


# Scenario schemas
class ScenarioCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    decision_type: DecisionType
    description: Optional[str] = None


class ScenarioResponse(BaseModel):
    id: int
    user_id: int
    name: str
    decision_type: DecisionType
    description: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# Simulation schemas
class SimulationInput(BaseModel):
    """User's natural language query for simulation"""
    query: str = Field(min_length=3, description="e.g., 'Move to Berlin vs Amsterdam'")
    time_horizon_years: int = Field(default=5, ge=1, le=30)
    monte_carlo_runs: Optional[int] = Field(default=1000, ge=100, le=10000)


class RelocationFactors(BaseModel):
    """Structured factors for relocation decision"""
    cities: List[str]
    current_salary: float
    expected_salary_change: Dict[str, float]  # city -> percentage
    cost_of_living: Dict[str, Dict[str, float]]  # city -> {rent, food, transport, etc.}
    tax_rates: Dict[str, float]  # city -> effective tax rate
    quality_of_life: Dict[str, float]  # city -> score 0-100


class PurchaseFactors(BaseModel):
    """Structured factors for purchase decision"""
    options: List[str]
    costs: Dict[str, float]
    maintenance_costs: Dict[str, float]
    depreciation_rates: Dict[str, float]
    utility_scores: Dict[str, float]


class JobFactors(BaseModel):
    """Structured factors for job decision"""
    options: List[str]
    salaries: Dict[str, float]
    growth_potential: Dict[str, float]
    work_life_balance: Dict[str, float]
    benefits: Dict[str, Dict[str, Any]]


class InvestmentFactors(BaseModel):
    """Structured factors for investment decision"""
    options: List[str]
    initial_amounts: Dict[str, float]
    expected_returns: Dict[str, float]
    volatility: Dict[str, float]
    liquidity: Dict[str, float]


class SimulationResult(BaseModel):
    """Complete simulation result"""
    scenario_id: int
    simulation_id: int
    status: SimulationStatus

    # Projections
    projections: Dict[str, List[Dict[str, float]]]  # option -> yearly projections

    # Monte Carlo results (if enabled)
    monte_carlo: Optional[Dict[str, Dict[str, float]]] = None  # option -> {mean, std, p5, p95}

    # AI-generated report
    summary: str
    risks: List[str]
    recommendation: str
    confidence_score: float = Field(ge=0, le=1)


class SimulationCreate(BaseModel):
    scenario_id: int
    input_data: SimulationInput


class SimulationResponse(BaseModel):
    id: int
    scenario_id: int
    status: SimulationStatus
    input_data: Dict[str, Any]
    result_json: Optional[Dict[str, Any]]
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


# ========== Модель для параметров быстрой симуляции (query) ==========
class QuickSimParams(BaseModel):
    """Query parameters for quick simulation endpoint /api/v1/simulate"""
    query: str = Field(..., min_length=3, description="Описание ситуации (минимум 3 символа)")
    decision_type: DecisionType
    time_horizon_years: int = Field(5, ge=1, le=20, description="Горизонт планирования в годах")


# API Response wrappers
class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None


class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    detail: Optional[str] = None