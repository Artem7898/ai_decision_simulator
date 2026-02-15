from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from app.db.session import get_db
from app.models.database import Scenario, Simulation, SimulationStatus, DecisionType as DBDecisionType
from app.schemas.schemas import (
    ScenarioCreate, ScenarioResponse,
    SimulationCreate, SimulationResponse, SimulationInput, SimulationResult,
    APIResponse, DecisionType, QuickSimParams
)
from app.services.llm_service import LLMService, DataService
from app.services.simulation_engine import SimulationEngine
from app.core.exceptions import DataNotFoundError, SimulationError

router = APIRouter()


# ==================== SCENARIOS ====================

@router.post("/scenarios", response_model=APIResponse)
async def create_scenario(
    scenario: ScenarioCreate,
    db: AsyncSession = Depends(get_db),
    user_id: int = 1  # TODO: Get from auth
):
    """Create a new decision scenario"""
    db_scenario = Scenario(
        user_id=user_id,
        name=scenario.name,
        decision_type=DBDecisionType(scenario.decision_type.value),
        description=scenario.description
    )
    db.add(db_scenario)
    await db.commit()
    await db.refresh(db_scenario)
    
    return APIResponse(
        success=True,
        message="Scenario created successfully",
        data=ScenarioResponse.model_validate(db_scenario).model_dump()
    )


@router.get("/scenarios", response_model=APIResponse)
async def list_scenarios(
    db: AsyncSession = Depends(get_db),
    user_id: int = 1  # TODO: Get from auth
):
    """List all scenarios for current user"""
    result = await db.execute(
        select(Scenario).where(Scenario.user_id == user_id).order_by(Scenario.created_at.desc())
    )
    scenarios = result.scalars().all()
    
    return APIResponse(
        success=True,
        message=f"Found {len(scenarios)} scenarios",
        data=[ScenarioResponse.model_validate(s).model_dump() for s in scenarios]
    )


@router.get("/scenarios/{scenario_id}", response_model=APIResponse)
async def get_scenario(
    scenario_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific scenario by ID"""
    result = await db.execute(
        select(Scenario).where(Scenario.id == scenario_id)
    )
    scenario = result.scalar_one_or_none()
    
    if not scenario:
        raise DataNotFoundError(f"Scenario {scenario_id} not found")
    
    return APIResponse(
        success=True,
        message="Scenario found",
        data=ScenarioResponse.model_validate(scenario).model_dump()
    )


@router.delete("/scenarios/{scenario_id}", response_model=APIResponse)
async def delete_scenario(
    scenario_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a scenario"""
    result = await db.execute(
        select(Scenario).where(Scenario.id == scenario_id)
    )
    scenario = result.scalar_one_or_none()
    
    if not scenario:
        raise DataNotFoundError(f"Scenario {scenario_id} not found")
    
    await db.delete(scenario)
    await db.commit()
    
    return APIResponse(
        success=True,
        message="Scenario deleted successfully",
        data=None
    )


# ==================== SIMULATIONS ====================

@router.post("/simulations", response_model=APIResponse)
async def create_simulation(
    simulation: SimulationCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create and run a new simulation"""
    
    # Get scenario
    result = await db.execute(
        select(Scenario).where(Scenario.id == simulation.scenario_id)
    )
    scenario = result.scalar_one_or_none()
    
    if not scenario:
        raise DataNotFoundError(f"Scenario {simulation.scenario_id} not found")
    
    # Create simulation record
    db_simulation = Simulation(
        scenario_id=scenario.id,
        input_data=simulation.input_data.model_dump(),
        status=SimulationStatus.PENDING
    )
    db.add(db_simulation)
    await db.commit()
    await db.refresh(db_simulation)
    
    try:
        # Update status to running
        db_simulation.status = SimulationStatus.RUNNING
        await db.commit()
        
        # Step 1: LLM structuring
        llm_service = LLMService()
        structured_data = await llm_service.structure_query(
            simulation.input_data.query,
            scenario.decision_type.value
        )
        
        # Step 2: Fetch external data
        data_service = DataService(db)
        external_data = {}
        
        # Get data based on decision type
        if scenario.decision_type == DBDecisionType.RELOCATION:
            cities = structured_data.get("cities", [])
            external_data["cost_of_living"] = {}
            external_data["tax_rates"] = {}
            for city in cities:
                external_data["cost_of_living"][city.lower()] = await data_service.get_cost_of_living(city)
                external_data["tax_rates"][city.lower()] = await data_service.get_tax_rates(city)
        
        # Step 3: Run simulation
        engine = SimulationEngine(
            time_horizon_years=simulation.input_data.time_horizon_years,
            monte_carlo_runs=simulation.input_data.monte_carlo_runs or 1000
        )
        
        simulation_results = await engine.run_simulation(
            DecisionType(scenario.decision_type.value),
            structured_data,
            external_data
        )
        
        # Step 4: Generate AI report
        report = await llm_service.generate_report(
            simulation.input_data.query,
            simulation_results
        )
        
        # Combine results
        final_results = {
            "structured_input": structured_data,
            "simulation_results": simulation_results,
            "ai_report": report
        }
        
        # Update simulation record
        db_simulation.result_json = final_results
        db_simulation.status = SimulationStatus.COMPLETED
        db_simulation.completed_at = datetime.utcnow()
        await db.commit()
        await db.refresh(db_simulation)
        
        return APIResponse(
            success=True,
            message="Simulation completed successfully",
            data=SimulationResponse.model_validate(db_simulation).model_dump()
        )
        
    except Exception as e:
        db_simulation.status = SimulationStatus.FAILED
        db_simulation.error_message = str(e)
        await db.commit()
        raise SimulationError(
            message="Simulation failed",
            detail=str(e)
        )


@router.get("/simulations/{simulation_id}", response_model=APIResponse)
async def get_simulation(
    simulation_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get simulation results"""
    result = await db.execute(
        select(Simulation).where(Simulation.id == simulation_id)
    )
    simulation = result.scalar_one_or_none()
    
    if not simulation:
        raise DataNotFoundError(f"Simulation {simulation_id} not found")
    
    return APIResponse(
        success=True,
        message="Simulation found",
        data=SimulationResponse.model_validate(simulation).model_dump()
    )


@router.get("/scenarios/{scenario_id}/simulations", response_model=APIResponse)
async def list_scenario_simulations(
    scenario_id: int,
    db: AsyncSession = Depends(get_db)
):
    """List all simulations for a scenario"""
    result = await db.execute(
        select(Simulation)
        .where(Simulation.scenario_id == scenario_id)
        .order_by(Simulation.created_at.desc())
    )
    simulations = result.scalars().all()
    
    return APIResponse(
        success=True,
        message=f"Found {len(simulations)} simulations",
        data=[SimulationResponse.model_validate(s).model_dump() for s in simulations]
    )


# ==================== QUICK SIMULATION ====================

@router.post("/simulate", response_model=APIResponse)
async def quick_simulation(
        params: QuickSimParams = Depends(),  # теперь FastAPI сам валидирует параметры
        db: AsyncSession = Depends(get_db),
        user_id: int = 1  # TODO: брать из аутентификации
):
    """Быстрая симуляция без предварительного создания сценария."""

    # Создаём сценарий
    scenario = Scenario(
        user_id=user_id,
        name=f"Quick: {params.query[:50]}...",
        decision_type=DBDecisionType(params.decision_type.value),
        description=params.query
    )
    db.add(scenario)
    await db.commit()
    await db.refresh(scenario)

    # Формируем входные данные для симуляции
    simulation_input = SimulationInput(
        query=params.query,
        time_horizon_years=params.time_horizon_years
        # monte_carlo_runs остаётся по умолчанию (1000)
    )

    simulation_create = SimulationCreate(
        scenario_id=scenario.id,
        input_data=simulation_input
    )

    # Вызываем существующий эндпоинт создания симуляции
    return await create_simulation(simulation_create, db)