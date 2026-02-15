import yfinance as yf
import pandas as pd
from typing import Dict, Any, List
from datetime import datetime, timedelta
import numpy as np


class FinancialDataService:
    """Service for fetching real financial data"""

    @staticmethod
    async def get_stock_data(ticker: str, years: int = 10) -> Dict[str, Any]:
        """
        Get historical data for a stock
        Args:
            ticker: Stock symbol (e.g., 'AAPL', 'GOOGL', 'MSFT')
            years: Number of years of historical data
        """
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period=f"{years}y")

            if hist.empty:
                return {
                    "error": f"No data found for {ticker}",
                    "ticker": ticker,
                    "current_price": 0,
                    "returns": 0,
                    "volatility": 0
                }

            # Calculate metrics
            returns = hist["Close"].pct_change().dropna()
            current_price = hist["Close"].iloc[-1]

            return {
                "ticker": ticker,
                "current_price": round(current_price, 2),
                "historical_data": {
                    "avg_annual_return": round(returns.mean() * 252, 4),
                    "annual_volatility": round(returns.std() * np.sqrt(252), 4),
                    "sharpe_ratio": round(returns.mean() / returns.std() * np.sqrt(252), 2),
                    "max_drawdown": round((hist["Close"] / hist["Close"].cummax() - 1).min(), 4),
                    "total_return": round((current_price / hist["Close"].iloc[0] - 1) * 100, 2)
                },
                "metadata": {
                    "period_years": years,
                    "data_points": len(hist),
                    "last_updated": datetime.utcnow().isoformat()
                }
            }
        except Exception as e:
            return {
                "error": str(e),
                "ticker": ticker
            }

    @staticmethod
    async def get_multiple_stocks_data(tickers: List[str], years: int = 5) -> Dict[str, Any]:
        """Get data for multiple stocks with correlation matrix"""
        all_data = {}
        prices_df = pd.DataFrame()

        for ticker in tickers:
            stock_data = await FinancialDataService.get_stock_data(ticker, years)
            if "error" not in stock_data:
                all_data[ticker] = stock_data

                # Get price history for correlation
                stock = yf.Ticker(ticker)
                hist = stock.history(period=f"{years}y")
                if not hist.empty:
                    prices_df[ticker] = hist["Close"]

        # Calculate correlation matrix if we have multiple tickers
        correlation_matrix = {}
        if len(prices_df.columns) > 1:
            corr = prices_df.pct_change().corr()
            correlation_matrix = corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool)).stack().to_dict()

        return {
            "stocks": all_data,
            "correlation_matrix": correlation_matrix,
            "portfolio_metrics": FinancialDataService._calculate_portfolio_metrics(all_data) if all_data else {}
        }

    @staticmethod
    def _calculate_portfolio_metrics(stocks_data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate basic portfolio metrics"""
        if not stocks_data:
            return {}

        returns = []
        volatilities = []

        for ticker, data in stocks_data.items():
            if "historical_data" in data:
                returns.append(data["historical_data"]["avg_annual_return"])
                volatilities.append(data["historical_data"]["annual_volatility"])

        if not returns:
            return {}

        # Simple equally weighted portfolio metrics
        avg_return = np.mean(returns)
        avg_volatility = np.mean(volatilities)

        return {
            "expected_return": round(avg_return, 4),
            "expected_volatility": round(avg_volatility, 4),
            "sharpe_ratio": round(avg_return / avg_volatility, 2) if avg_volatility > 0 else 0
        }

    @staticmethod
    async def get_bond_yield(bond_type: str = "10y") -> Dict[str, Any]:
        """Get current bond yields"""
        # Note: yfinance can get treasury yields
        try:
            # For US Treasury yields
            tickers = {
                "10y": "^TNX",  # 10-Year Treasury Yield
                "5y": "^FVX",  # 5-Year Treasury Yield
                "2y": "^IRX",  # 13-Week Treasury Yield
            }

            ticker = tickers.get(bond_type, "^TNX")
            bond = yf.Ticker(ticker)
            hist = bond.history(period="1mo")

            if hist.empty:
                return {
                    "bond_type": bond_type,
                    "current_yield": 0.04,  # Default fallback
                    "source": "fallback"
                }

            current_yield = hist["Close"].iloc[-1] / 100  # Convert from percentage

            return {
                "bond_type": bond_type,
                "current_yield": round(current_yield, 4),
                "current_yield_percent": round(current_yield * 100, 2),
                "source": "yfinance",
                "last_updated": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "bond_type": bond_type,
                "current_yield": 0.04,  # Fallback
                "error": str(e),
                "source": "fallback"
            }