import httpx
import json
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.config import get_settings
from app.core.exceptions import LLMProcessingError
from app.models.database import CachedData

settings = get_settings()


class LLMService:
    """Service for LLM interactions"""

    STRUCTURING_PROMPT = """You are an expert decision analyst. Parse the user's decision query and extract structured factors.

User Query: {query}
Decision Type: {decision_type}

Extract and return a JSON object with the following structure based on decision type:

For RELOCATION:
{{
    "cities": ["city1", "city2"],
    "factors_to_compare": ["cost_of_living", "salary", "taxes", "quality_of_life"],
    "user_context": {{
        "current_location": "...",
        "profession": "...",
        "priorities": ["..."]
    }}
}}

For PURCHASE:
{{
    "options": ["option1", "option2"],
    "budget": 0,
    "factors_to_compare": ["price", "maintenance", "depreciation", "utility"],
    "user_context": {{
        "current_situation": "...",
        "needs": ["..."],
        "preferences": ["..."]
    }}
}}

For JOB:
{{
    "options": ["job1", "job2"],
    "factors_to_compare": ["salary", "growth", "work_life_balance", "benefits"],
    "user_context": {{
        "current_job": "...",
        "experience": "...",
        "career_goals": ["..."]
    }}
}}

For INVESTMENT:
{{
    "options": ["investment1", "investment2"],
    "amount": 10000,
    "risk_tolerance": "low|medium|high",
    "factors_to_compare": ["returns", "volatility", "liquidity", "time_horizon"],
    "user_context": {{
        "investment_experience": "...",
        "age": ...,
        "financial_goals": ["..."]
    }}
}}

Return ONLY valid JSON, no additional text."""

    REPORT_PROMPT = """You are an expert decision analyst. Based on the simulation results, generate a comprehensive report.

Decision Query: {query}
Decision Type: {decision_type}
Simulation Results: {results}

Generate a report with:
1. **Summary**: A clear 2-3 sentence summary of the analysis
2. **Risks**: List of 3-5 key risks for each option
3. **Recommendation**: Your expert recommendation with reasoning
4. **Confidence Score**: A score from 0 to 1 indicating confidence in the recommendation

Return as JSON:
{{
    "summary": "...",
    "risks": ["risk1", "risk2", ...],
    "recommendation": "...",
    "confidence_score": 0.85
}}"""

    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.model = settings.LLM_MODEL

    async def structure_query(self, query: str, decision_type: str) -> Dict[str, Any]:
        """Parse user query into structured factors using LLM"""
        prompt = self.STRUCTURING_PROMPT.format(
            query=query,
            decision_type=decision_type
        )

        response = await self._call_llm(prompt, decision_type)
        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            raise LLMProcessingError(
                message="Failed to parse LLM response",
                detail=str(e)
            )

    async def generate_report(self, query: str, results: Dict[str, Any], decision_type: str = None) -> Dict[str, Any]:
        """Generate AI report from simulation results"""
        prompt = self.REPORT_PROMPT.format(
            query=query,
            decision_type=decision_type or "general",
            results=json.dumps(results, indent=2)
        )

        response = await self._call_llm(prompt, "report")
        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            raise LLMProcessingError(
                message="Failed to parse report",
                detail=str(e)
            )

    async def _call_llm(self, prompt: str, context: str = None) -> str:
        """Make API call to LLM"""
        if not self.api_key:
            # Mock response for development
            return self._mock_response(prompt, context)

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.7
                    },
                    timeout=60.0
                )
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
            except httpx.HTTPError as e:
                raise LLMProcessingError(
                    message="LLM API call failed",
                    detail=str(e)
                )

    def _mock_response(self, prompt: str, context: str = None) -> str:
        """Mock response for development without API key"""
        prompt_lower = prompt.lower()

        # Определяем тип решения
        if context:
            # Используем предоставленный контекст
            decision_type = context.lower()
        elif "decision type:" in prompt_lower:
            # Извлекаем тип решения из промпта
            import re
            match = re.search(r'decision type:\s*(\w+)', prompt_lower)
            decision_type = match.group(1) if match else None
        else:
            decision_type = None

        # Для отчетов
        if "summary" in prompt_lower or "report" in prompt_lower:
            return json.dumps({
                "summary": "Based on the analysis, both options present viable paths with distinct trade-offs.",
                "risks": [
                    "Market volatility may affect projections",
                    "Regulations may change",
                    "External factors may vary over time"
                ],
                "recommendation": "Consider the option with better long-term financial outlook while weighing personal preferences.",
                "confidence_score": 0.75
            })

        # Для структурирования по типам решений
        if decision_type == "relocation" or ("relocation" in prompt_lower and "example" not in prompt_lower):
            return json.dumps({
                "cities": ["Berlin", "Amsterdam"],
                "factors_to_compare": ["cost_of_living", "salary", "taxes", "quality_of_life"],
                "user_context": {
                    "current_location": "Unknown",
                    "profession": "Tech professional",
                    "priorities": ["career growth", "quality of life"]
                }
            })
        elif decision_type == "investment" or ("investment" in prompt_lower and "example" not in prompt_lower):
            # Проверяем содержание запроса для более точного ответа
            if "stocks" in prompt_lower or "bonds" in prompt_lower:
                options = ["stocks", "bonds"]
            elif "real estate" in prompt_lower or "property" in prompt_lower:
                options = ["real estate investment", "stock market"]
            elif "crypto" in prompt_lower or "bitcoin" in prompt_lower:
                options = ["cryptocurrency", "traditional investments"]
            else:
                options = ["Option A", "Option B"]

            return json.dumps({
                "options": options,
                "amount": 10000,
                "risk_tolerance": "medium",
                "factors_to_compare": ["returns", "volatility", "liquidity", "time_horizon"],
                "user_context": {
                    "investment_experience": "beginner" if "beginner" in prompt_lower else "intermediate",
                    "age": 35,
                    "financial_goals": ["retirement", "wealth accumulation"]
                }
            })
        elif decision_type == "purchase" or ("purchase" in prompt_lower and "example" not in prompt_lower):
            if "car" in prompt_lower or "vehicle" in prompt_lower:
                options = ["Electric Car", "Gasoline Car"]
            elif "house" in prompt_lower or "apartment" in prompt_lower:
                options = ["House in suburbs", "Apartment in city center"]
            else:
                options = ["Option X", "Option Y"]

            return json.dumps({
                "options": options,
                "budget": 50000,
                "factors_to_compare": ["price", "maintenance", "depreciation", "utility"],
                "user_context": {
                    "current_situation": "Looking to upgrade",
                    "needs": ["reliability", "cost-effectiveness"],
                    "preferences": ["modern design", "efficiency"]
                }
            })
        elif decision_type == "job" or ("job" in prompt_lower and "example" not in prompt_lower):
            return json.dumps({
                "options": ["Software Engineer at Company A", "Data Scientist at Company B"],
                "factors_to_compare": ["salary", "growth", "work_life_balance", "benefits"],
                "user_context": {
                    "current_job": "Developer",
                    "experience": "5 years",
                    "career_goals": ["leadership", "technical expertise"]
                }
            })
        else:
            # По умолчанию для инвестиций
            return json.dumps({
                "options": ["stocks", "bonds"],
                "amount": 10000,
                "risk_tolerance": "medium",
                "factors_to_compare": ["returns", "volatility", "liquidity"],
                "user_context": {
                    "investment_experience": "intermediate",
                    "age": 35,
                    "financial_goals": ["growth", "security"]
                }
            })


class DataService:
    """Service for fetching external data"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_cost_of_living(self, city: str) -> Dict[str, float]:
        """Fetch cost of living data for a city"""
        cache_key = f"col_{city.lower()}"

        # Check cache
        cached = await self._get_cached(cache_key)
        if cached:
            return cached

        # Mock data (replace with actual API call)
        data = self._mock_cost_of_living(city)

        # Cache the data
        await self._set_cached(cache_key, data, source="numbeo")

        return data

    async def get_tax_rates(self, city: str) -> Dict[str, float]:
        """Fetch tax rates for a city/country"""
        cache_key = f"tax_{city.lower()}"

        cached = await self._get_cached(cache_key)
        if cached:
            return cached

        # Mock data
        data = self._mock_tax_rates(city)
        await self._set_cached(cache_key, data, source="internal")

        return data

    async def get_financial_data(self, investment_type: str) -> Dict[str, Any]:
        """Fetch financial data for investments"""
        cache_key = f"fin_{investment_type.lower()}"

        cached = await self._get_cached(cache_key)
        if cached:
            return cached

        # Mock financial data
        data = self._mock_financial_data(investment_type)
        await self._set_cached(cache_key, data, source="financial_api")

        return data

    async def _get_cached(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get data from cache"""
        result = await self.db.execute(
            select(CachedData).where(
                CachedData.cache_key == cache_key,
                CachedData.expires_at > datetime.utcnow()
            )
        )
        cached = result.scalar_one_or_none()
        return cached.data if cached else None

    async def _set_cached(self, cache_key: str, data: Dict[str, Any], source: str):
        """Set data in cache"""
        expires_at = datetime.utcnow() + timedelta(seconds=settings.CACHE_TTL_SECONDS)

        cached = CachedData(
            cache_key=cache_key,
            data=data,
            source=source,
            expires_at=expires_at
        )
        self.db.add(cached)
        await self.db.commit()

    def _mock_cost_of_living(self, city: str) -> Dict[str, float]:
        """Mock cost of living data"""
        data = {
            "berlin": {"rent": 1200, "food": 400, "transport": 86, "utilities": 200, "entertainment": 150},
            "amsterdam": {"rent": 1800, "food": 450, "transport": 100, "utilities": 180, "entertainment": 200},
            "london": {"rent": 2200, "food": 500, "transport": 150, "utilities": 200, "entertainment": 250},
            "paris": {"rent": 1600, "food": 480, "transport": 75, "utilities": 170, "entertainment": 180},
        }
        return data.get(city.lower(),
                        {"rent": 1000, "food": 350, "transport": 80, "utilities": 150, "entertainment": 100})

    def _mock_tax_rates(self, city: str) -> Dict[str, float]:
        """Mock tax rates"""
        data = {
            "berlin": {"income_tax": 0.42, "social_security": 0.20, "effective_rate": 0.35},
            "amsterdam": {"income_tax": 0.495, "social_security": 0.15, "effective_rate": 0.38},
            "london": {"income_tax": 0.45, "social_security": 0.12, "effective_rate": 0.32},
            "paris": {"income_tax": 0.45, "social_security": 0.22, "effective_rate": 0.40},
        }
        return data.get(city.lower(), {"income_tax": 0.30, "social_security": 0.15, "effective_rate": 0.30})

    def _mock_financial_data(self, investment_type: str) -> Dict[str, Any]:
        """Mock financial data for investments"""
        data = {
            "stocks": {
                "historical_returns": 0.10,
                "volatility": 0.20,
                "sharpe_ratio": 0.50,
                "max_drawdown": -0.33,
                "correlation": {
                    "bonds": -0.20,
                    "real_estate": 0.60,
                    "gold": 0.15
                }
            },
            "bonds": {
                "historical_returns": 0.05,
                "volatility": 0.05,
                "sharpe_ratio": 1.00,
                "max_drawdown": -0.08,
                "correlation": {
                    "stocks": -0.20,
                    "real_estate": 0.10,
                    "gold": 0.05
                }
            },
            "real estate": {
                "historical_returns": 0.07,
                "volatility": 0.10,
                "sharpe_ratio": 0.70,
                "max_drawdown": -0.20,
                "correlation": {
                    "stocks": 0.60,
                    "bonds": 0.10,
                    "gold": 0.20
                }
            },
            "crypto": {
                "historical_returns": 0.15,
                "volatility": 0.50,
                "sharpe_ratio": 0.30,
                "max_drawdown": -0.75,
                "correlation": {
                    "stocks": 0.25,
                    "bonds": -0.10,
                    "gold": 0.10
                }
            }
        }
        return data.get(investment_type.lower(), {
            "historical_returns": 0.06,
            "volatility": 0.12,
            "sharpe_ratio": 0.50,
            "max_drawdown": -0.15,
            "correlation": {}
        })