from celery import Celery
from datetime import datetime
import json

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "decision_simulator",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,  # 10 minutes max
    worker_prefetch_multiplier=1,
)


@celery_app.task(bind=True, name="run_heavy_simulation")
def run_heavy_simulation(self, simulation_id: int, input_data: dict):
    """
    Background task for heavy simulations (Monte Carlo with many runs).
    Use this for simulations that might take > 30 seconds.
    """
    from app.db.session import AsyncSessionLocal
    from app.models.database import Simulation, Scenario, SimulationStatus
    from app.services.simulation_engine import SimulationEngine
    from app.services.llm_service import LLMService, DataService
    from app.schemas.schemas import DecisionType
    import asyncio
    
    async def _run():
        async with AsyncSessionLocal() as db:
            # Get simulation
            from sqlalchemy import select
            result = await db.execute(
                select(Simulation).where(Simulation.id == simulation_id)
            )
            simulation = result.scalar_one_or_none()
            
            if not simulation:
                return {"error": f"Simulation {simulation_id} not found"}
            
            # Get scenario
            result = await db.execute(
                select(Scenario).where(Scenario.id == simulation.scenario_id)
            )
            scenario = result.scalar_one()
            
            try:
                simulation.status = SimulationStatus.RUNNING
                await db.commit()
                
                # Update task progress
                self.update_state(state="PROGRESS", meta={"step": "structuring"})
                
                llm_service = LLMService()
                structured_data = await llm_service.structure_query(
                    input_data["query"],
                    scenario.decision_type.value
                )
                
                self.update_state(state="PROGRESS", meta={"step": "fetching_data"})
                
                data_service = DataService(db)
                external_data = {}
                
                if scenario.decision_type.value == "relocation":
                    cities = structured_data.get("cities", [])
                    external_data["cost_of_living"] = {}
                    external_data["tax_rates"] = {}
                    for city in cities:
                        external_data["cost_of_living"][city.lower()] = await data_service.get_cost_of_living(city)
                        external_data["tax_rates"][city.lower()] = await data_service.get_tax_rates(city)
                
                self.update_state(state="PROGRESS", meta={"step": "running_simulation"})
                
                engine = SimulationEngine(
                    time_horizon_years=input_data.get("time_horizon_years", 5),
                    monte_carlo_runs=input_data.get("monte_carlo_runs", 1000)
                )
                
                simulation_results = await engine.run_simulation(
                    DecisionType(scenario.decision_type.value),
                    structured_data,
                    external_data
                )
                
                self.update_state(state="PROGRESS", meta={"step": "generating_report"})
                
                report = await llm_service.generate_report(
                    input_data["query"],
                    simulation_results
                )
                
                final_results = {
                    "structured_input": structured_data,
                    "simulation_results": simulation_results,
                    "ai_report": report
                }
                
                simulation.result_json = final_results
                simulation.status = SimulationStatus.COMPLETED
                simulation.completed_at = datetime.utcnow()
                await db.commit()
                
                return {"success": True, "simulation_id": simulation_id}
                
            except Exception as e:
                simulation.status = SimulationStatus.FAILED
                simulation.error_message = str(e)
                await db.commit()
                return {"error": str(e)}
    
    return asyncio.get_event_loop().run_until_complete(_run())


@celery_app.task(name="cleanup_old_cache")
def cleanup_old_cache():
    """Periodic task to clean up expired cache entries"""
    from app.db.session import AsyncSessionLocal
    from app.models.database import CachedData
    from sqlalchemy import delete
    import asyncio
    
    async def _cleanup():
        async with AsyncSessionLocal() as db:
            await db.execute(
                delete(CachedData).where(CachedData.expires_at < datetime.utcnow())
            )
            await db.commit()
    
    asyncio.get_event_loop().run_until_complete(_cleanup())
    return {"status": "cleaned"}


# Celery Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    "cleanup-cache-daily": {
        "task": "cleanup_old_cache",
        "schedule": 86400.0,  # Daily
    },
}
