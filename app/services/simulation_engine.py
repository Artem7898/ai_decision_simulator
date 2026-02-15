import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime
from app.schemas.schemas import DecisionType


class SimulationEngine:
    """Engine for running financial simulations"""
    
    def __init__(
        self,
        time_horizon_years: int = 5,
        monte_carlo_runs: int = 1000
    ):
        self.time_horizon = time_horizon_years
        self.monte_carlo_runs = monte_carlo_runs
    
    async def run_simulation(
        self,
        decision_type: DecisionType,
        structured_data: Dict[str, Any],
        external_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run simulation based on decision type"""
        
        if decision_type == DecisionType.RELOCATION:
            return await self._simulate_relocation(structured_data, external_data)
        elif decision_type == DecisionType.PURCHASE:
            return await self._simulate_purchase(structured_data, external_data)
        elif decision_type == DecisionType.JOB:
            return await self._simulate_job(structured_data, external_data)
        elif decision_type == DecisionType.INVESTMENT:
            return await self._simulate_investment(structured_data, external_data)
        else:
            raise ValueError(f"Unknown decision type: {decision_type}")
    
    async def _simulate_relocation(
        self,
        structured_data: Dict[str, Any],
        external_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Simulate relocation decision"""
        cities = structured_data.get("cities", [])
        projections = {}
        monte_carlo_results = {}
        
        for city in cities:
            city_lower = city.lower()
            col = external_data.get("cost_of_living", {}).get(city_lower, {})
            tax = external_data.get("tax_rates", {}).get(city_lower, {})
            
            # Calculate yearly costs
            monthly_cost = sum(col.values()) if col else 2000
            yearly_cost = monthly_cost * 12
            effective_tax = tax.get("effective_rate", 0.30)
            
            # Base salary assumption (can be customized)
            base_salary = structured_data.get("user_context", {}).get("salary", 80000)
            
            # Generate yearly projections
            yearly_projections = []
            for year in range(1, self.time_horizon + 1):
                # Assume 3% inflation, 2% salary growth
                inflation_factor = 1.03 ** year
                salary_factor = 1.02 ** year
                
                adjusted_salary = base_salary * salary_factor
                adjusted_cost = yearly_cost * inflation_factor
                net_income = adjusted_salary * (1 - effective_tax)
                savings = net_income - adjusted_cost
                
                yearly_projections.append({
                    "year": year,
                    "gross_income": round(adjusted_salary, 2),
                    "net_income": round(net_income, 2),
                    "total_expenses": round(adjusted_cost, 2),
                    "savings": round(savings, 2),
                    "cumulative_savings": round(savings * year, 2)  # Simplified
                })
            
            projections[city] = yearly_projections
            
            # Monte Carlo simulation
            mc_results = self._run_monte_carlo_savings(
                base_salary, yearly_cost, effective_tax
            )
            monte_carlo_results[city] = mc_results
        
        return {
            "projections": projections,
            "monte_carlo": monte_carlo_results,
            "metadata": {
                "time_horizon_years": self.time_horizon,
                "monte_carlo_runs": self.monte_carlo_runs,
                "simulation_date": datetime.utcnow().isoformat()
            }
        }
    
    async def _simulate_purchase(
        self,
        structured_data: Dict[str, Any],
        external_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Simulate purchase decision"""
        options = structured_data.get("options", [])
        budget = structured_data.get("budget", 50000)
        projections = {}
        
        for i, option in enumerate(options):
            # Mock cost data
            initial_cost = budget * (0.8 + i * 0.2)
            yearly_maintenance = initial_cost * 0.05
            depreciation_rate = 0.15
            
            yearly_projections = []
            current_value = initial_cost
            total_cost = initial_cost
            
            for year in range(1, self.time_horizon + 1):
                current_value *= (1 - depreciation_rate)
                total_cost += yearly_maintenance
                
                yearly_projections.append({
                    "year": year,
                    "current_value": round(current_value, 2),
                    "maintenance_cost": round(yearly_maintenance, 2),
                    "total_cost_to_date": round(total_cost, 2),
                    "net_value": round(current_value - total_cost, 2)
                })
            
            projections[option] = yearly_projections
        
        return {
            "projections": projections,
            "monte_carlo": None,
            "metadata": {
                "time_horizon_years": self.time_horizon,
                "simulation_date": datetime.utcnow().isoformat()
            }
        }
    
    async def _simulate_job(
        self,
        structured_data: Dict[str, Any],
        external_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Simulate job decision"""
        options = structured_data.get("options", [])
        projections = {}
        monte_carlo_results = {}
        
        for i, option in enumerate(options):
            base_salary = 70000 + i * 15000  # Mock salaries
            growth_rate = 0.05 + i * 0.02
            
            yearly_projections = []
            cumulative_earnings = 0
            
            for year in range(1, self.time_horizon + 1):
                current_salary = base_salary * ((1 + growth_rate) ** year)
                cumulative_earnings += current_salary
                
                yearly_projections.append({
                    "year": year,
                    "salary": round(current_salary, 2),
                    "cumulative_earnings": round(cumulative_earnings, 2),
                    "growth_rate": round(growth_rate * 100, 1)
                })
            
            projections[option] = yearly_projections
            
            # Monte Carlo for salary growth uncertainty
            mc_results = self._run_monte_carlo_salary(base_salary, growth_rate)
            monte_carlo_results[option] = mc_results
        
        return {
            "projections": projections,
            "monte_carlo": monte_carlo_results,
            "metadata": {
                "time_horizon_years": self.time_horizon,
                "monte_carlo_runs": self.monte_carlo_runs,
                "simulation_date": datetime.utcnow().isoformat()
            }
        }
    
    async def _simulate_investment(
        self,
        structured_data: Dict[str, Any],
        external_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Simulate investment decision"""
        options = structured_data.get("options", [])
        amount = structured_data.get("amount", 10000)
        projections = {}
        monte_carlo_results = {}
        
        # Mock investment parameters
        investment_params = {
            "stocks": {"return": 0.10, "volatility": 0.20},
            "bonds": {"return": 0.05, "volatility": 0.05},
            "real_estate": {"return": 0.07, "volatility": 0.10},
            "crypto": {"return": 0.15, "volatility": 0.50},
        }
        
        for option in options:
            option_lower = option.lower()
            params = investment_params.get(
                option_lower,
                {"return": 0.06, "volatility": 0.12}
            )
            
            expected_return = params["return"]
            volatility = params["volatility"]
            
            # Deterministic projection
            yearly_projections = []
            current_value = amount
            
            for year in range(1, self.time_horizon + 1):
                current_value *= (1 + expected_return)
                yearly_projections.append({
                    "year": year,
                    "value": round(current_value, 2),
                    "total_return": round(current_value - amount, 2),
                    "return_percentage": round((current_value / amount - 1) * 100, 2)
                })
            
            projections[option] = yearly_projections
            
            # Monte Carlo simulation
            mc_results = self._run_monte_carlo_investment(
                amount, expected_return, volatility
            )
            monte_carlo_results[option] = mc_results
        
        return {
            "projections": projections,
            "monte_carlo": monte_carlo_results,
            "metadata": {
                "time_horizon_years": self.time_horizon,
                "monte_carlo_runs": self.monte_carlo_runs,
                "initial_amount": amount,
                "simulation_date": datetime.utcnow().isoformat()
            }
        }
    
    def _run_monte_carlo_savings(
        self,
        base_salary: float,
        yearly_cost: float,
        tax_rate: float
    ) -> Dict[str, float]:
        """Run Monte Carlo simulation for savings projection"""
        final_savings = []
        
        for _ in range(self.monte_carlo_runs):
            cumulative_savings = 0
            salary = base_salary
            cost = yearly_cost
            
            for year in range(self.time_horizon):
                # Random factors
                salary_growth = np.random.normal(0.02, 0.02)
                inflation = np.random.normal(0.03, 0.01)
                
                salary *= (1 + salary_growth)
                cost *= (1 + inflation)
                
                net_income = salary * (1 - tax_rate)
                cumulative_savings += net_income - cost
            
            final_savings.append(cumulative_savings)
        
        return {
            "mean": round(np.mean(final_savings), 2),
            "std": round(np.std(final_savings), 2),
            "p5": round(np.percentile(final_savings, 5), 2),
            "p25": round(np.percentile(final_savings, 25), 2),
            "p50": round(np.percentile(final_savings, 50), 2),
            "p75": round(np.percentile(final_savings, 75), 2),
            "p95": round(np.percentile(final_savings, 95), 2)
        }
    
    def _run_monte_carlo_salary(
        self,
        base_salary: float,
        expected_growth: float
    ) -> Dict[str, float]:
        """Run Monte Carlo for salary projections"""
        final_salaries = []
        
        for _ in range(self.monte_carlo_runs):
            salary = base_salary
            for year in range(self.time_horizon):
                growth = np.random.normal(expected_growth, 0.03)
                salary *= (1 + growth)
            final_salaries.append(salary)
        
        return {
            "mean": round(np.mean(final_salaries), 2),
            "std": round(np.std(final_salaries), 2),
            "p5": round(np.percentile(final_salaries, 5), 2),
            "p95": round(np.percentile(final_salaries, 95), 2)
        }
    
    def _run_monte_carlo_investment(
        self,
        initial_amount: float,
        expected_return: float,
        volatility: float
    ) -> Dict[str, float]:
        """Run Monte Carlo for investment projections"""
        final_values = []
        
        for _ in range(self.monte_carlo_runs):
            value = initial_amount
            for year in range(self.time_horizon):
                annual_return = np.random.normal(expected_return, volatility)
                value *= (1 + annual_return)
            final_values.append(value)
        
        return {
            "mean": round(np.mean(final_values), 2),
            "std": round(np.std(final_values), 2),
            "p5": round(np.percentile(final_values, 5), 2),
            "p25": round(np.percentile(final_values, 25), 2),
            "p50": round(np.percentile(final_values, 50), 2),
            "p75": round(np.percentile(final_values, 75), 2),
            "p95": round(np.percentile(final_values, 95), 2),
            "prob_loss": round(np.mean(np.array(final_values) < initial_amount) * 100, 2)
        }
