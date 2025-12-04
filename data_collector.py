import yfinance as yf
from bs4 import BeautifulSoup
import requests
import pandas as pd
from datetime import datetime, timedelta
from stock_universe import STOCK_UNIVERSE
import time
import random

# Sample data for fallback when market is closed
SAMPLE_STOCKS = [
    {
        "symbol": "RELIANCE", "name": "Reliance Industries", "sector": "Energy",
        "current_price": 2850.50, "pe_ratio": 22.5, "pb_ratio": 3.2, "market_cap": 3850000000000,
        "beta": 1.05, "dividend_yield": 0.75, "week52_high": 3050.0, "week52_low": 2450.0,
        "month_return": 5.2, "volatility": 2.1
    },
    {
        "symbol": "TCS", "name": "Tata Consultancy Services", "sector": "IT",
        "current_price": 3850.75, "pe_ratio": 24.3, "pb_ratio": 5.1, "market_cap": 4200000000000,
        "beta": 0.95, "dividend_yield": 1.2, "week52_high": 4100.0, "week52_low": 3200.0,
        "month_return": 3.8, "volatility": 1.8
    },
    {
        "symbol": "HDFCBANK", "name": "HDFC Bank", "sector": "Finance",
        "current_price": 1850.25, "pe_ratio": 18.9, "pb_ratio": 2.8, "market_cap": 2800000000000,
        "beta": 1.15, "dividend_yield": 2.1, "week52_high": 2100.0, "week52_low": 1500.0,
        "month_return": 6.5, "volatility": 2.3
    },
    {
        "symbol": "INFY", "name": "Infosys", "sector": "IT",
        "current_price": 1925.50, "pe_ratio": 26.1, "pb_ratio": 4.5, "market_cap": 1650000000000,
        "beta": 0.88, "dividend_yield": 1.5, "week52_high": 2150.0, "week52_low": 1650.0,
        "month_return": 2.1, "volatility": 1.9
    },
    {
        "symbol": "ICICIBANK", "name": "ICICI Bank", "sector": "Finance",
        "current_price": 1425.80, "pe_ratio": 17.2, "pb_ratio": 2.4, "market_cap": 1950000000000,
        "beta": 1.25, "dividend_yield": 2.8, "week52_high": 1650.0, "week52_low": 1100.0,
        "month_return": 8.3, "volatility": 2.5
    },
    {
        "symbol": "HINDUNILVR", "name": "Hindustan Unilever", "sector": "Consumer",
        "current_price": 2285.40, "pe_ratio": 45.8, "pb_ratio": 8.2, "market_cap": 520000000000,
        "beta": 0.72, "dividend_yield": 1.8, "week52_high": 2500.0, "week52_low": 1950.0,
        "month_return": 1.2, "volatility": 1.5
    },
    {
        "symbol": "SBIN", "name": "State Bank of India", "sector": "Finance",
        "current_price": 680.50, "pe_ratio": 13.5, "pb_ratio": 1.1, "market_cap": 1850000000000,
        "beta": 1.35, "dividend_yield": 3.2, "week52_high": 850.0, "week52_low": 500.0,
        "month_return": 7.8, "volatility": 2.8
    },
    {
        "symbol": "BHARTIARTL", "name": "Bharti Airtel", "sector": "Telecom",
        "current_price": 1085.25, "pe_ratio": 28.3, "pb_ratio": 1.9, "market_cap": 950000000000,
        "beta": 1.02, "dividend_yield": 0.5, "week52_high": 1200.0, "week52_low": 850.0,
        "month_return": 4.5, "volatility": 2.2
    },
    {
        "symbol": "KOTAKBANK", "name": "Kotak Mahindra Bank", "sector": "Finance",
        "current_price": 1950.75, "pe_ratio": 19.8, "pb_ratio": 3.1, "market_cap": 680000000000,
        "beta": 1.18, "dividend_yield": 2.3, "week52_high": 2200.0, "week52_low": 1600.0,
        "month_return": 5.9, "volatility": 2.4
    },
    {
        "symbol": "ITC", "name": "ITC Limited", "sector": "Consumer",
        "current_price": 425.30, "pe_ratio": 15.2, "pb_ratio": 1.8, "market_cap": 850000000000,
        "beta": 0.95, "dividend_yield": 4.5, "week52_high": 500.0, "week52_low": 350.0,
        "month_return": 3.2, "volatility": 1.6
    },
]

class StockDataCollector:
    def __init__(self):
        self.stocks = STOCK_UNIVERSE
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }

    def get_market_indices(self):
        """Fetch indices or return dummy data"""
        try:
            print("  Attempting to fetch live indices...")
            nifty = yf.Ticker("^NSEI").history(period="1mo")
            sensex = yf.Ticker("^BSESN").history(period="1mo")
            
            if len(nifty) > 2 and len(sensex) > 2:
                def summarize(df):
                    cur = float(df["Close"].iloc[-1])
                    prev = float(df["Close"].iloc[-2])
                    ch = cur - prev
                    ch_pct = ch / prev * 100
                    return {"current": round(cur, 2), "prev_close": round(prev, 2),
                            "change": round(ch, 2), "change_pct": round(ch_pct, 2)}
                return {"nifty": summarize(nifty), "sensex": summarize(sensex)}
        except Exception as e:
            print(f"  Live fetch failed: {e}")
        
        print("  Using fallback index data")
        return {
            "nifty": {"current": 24550.0, "prev_close": 24350.0, "change": 200.0, "change_pct": 0.82},
            "sensex": {"current": 81200.0, "prev_close": 80850.0, "change": 350.0, "change_pct": 0.43}
        }

    def get_sample_data(self):
        """Return sample stocks for testing/non-market hours"""
        print("  Using sample stock data (market closed or data unavailable)")
        return SAMPLE_STOCKS

    def get_stock_data_with_retry(self, symbol: str, max_retries=2):
        """Fetch stock data with retry logic"""
        for attempt in range(max_retries):
            try:
                time.sleep(random.uniform(0.5, 1.5))
                
                today = datetime.now().date()
                start = today - timedelta(days=45)

                hist_daily = yf.download(
                    symbol, start=start, end=today + timedelta(days=1), 
                    interval="1d", progress=False, timeout=10
                )

                if hist_daily.empty or len(hist_daily) < 5:
                    return None

                ticker = yf.Ticker(symbol)
                info = ticker.info
                
                current_price = float(hist_daily["Close"].iloc[-1])
                month_return = ((hist_daily["Close"].iloc[-1] - hist_daily["Close"].iloc[0]) / 
                               hist_daily["Close"].iloc[0] * 100)
                volatility = hist_daily["Close"].pct_change().std() * 100

                return {
                    "symbol": symbol.replace(".NS", ""),
                    "name": info.get("shortName", symbol.replace(".NS", "")),
                    "sector": info.get("sector", "N/A"),
                    "current_price": round(current_price, 2),
                    "pe_ratio": float(info.get("trailingPE") or 0),
                    "pb_ratio": float(info.get("priceToBook") or 0),
                    "market_cap": int(info.get("marketCap") or 0),
                    "beta": float(info.get("beta") or 1),
                    "dividend_yield": float(info.get("dividendYield") or 0) * 100,
                    "week52_high": float(info.get("fiftyTwoWeekHigh") or current_price),
                    "week52_low": float(info.get("fiftyTwoWeekLow") or current_price),
                    "month_return": round(float(month_return), 2),
                    "volatility": round(float(volatility), 2),
                }
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(2)
                continue
        
        return None

    def scrape_market_news(self, limit: int = 10):
        urls = [
            "https://economictimes.indiatimes.com/markets/stocks/news",
            "https://www.moneycontrol.com/news/business/markets/",
        ]
        news = []
        for url in urls:
            try:
                r = requests.get(url, headers=self.headers, timeout=10)
                soup = BeautifulSoup(r.text, "lxml")
                for h in soup.find_all(["h2", "h3"], limit=limit):
                    text = h.get_text(strip=True)
                    if text and len(text) > 25:
                        news.append(text)
            except Exception as e:
                print(f"News error: {str(e)[:50]}")
        return list(dict.fromkeys(news))[:limit]

    def get_all_stocks_snapshot(self):
        """Fetch real data or use sample data"""
        data = []
        print("\n  Attempting to fetch live stock data...")
        
        for idx, sym in enumerate(self.stocks[:30], 1):  # Try first 30 only
            print(f"  [{idx}/30] Fetching: {sym}")
            stock_data = self.get_stock_data_with_retry(sym)
            if stock_data:
                data.append(stock_data)
        
        if len(data) < 5:  # If too few real stocks, use sample data
            print(f"\n  Only fetched {len(data)} real stocks. Using sample data instead.")
            data = self.get_sample_data()
        else:
            print(f"\n  Successfully fetched: {len(data)} stocks")
        
        return data

    def sector_performance(self, all_data):
        df = pd.DataFrame(all_data)
        if df.empty:
            return {}
        grp = df.groupby("sector")["month_return"].mean().sort_values(ascending=False)
        return grp.to_dict()
