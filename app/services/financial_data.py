import yfinance as yf
import pandas as pd

async def get_stock_data(ticker: str, years: int = 10):
    stock = yf.Ticker(ticker)
    hist = stock.history(period=f"{years}y")
    return {
        "avg_return": hist["Close"].pct_change().mean(),
        "volatility": hist["Close"].pct_change().std(),
        "sharpe_ratio": hist["Close"].pct_change().mean() / hist["Close"].pct_change().std()
    }