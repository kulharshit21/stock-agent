import yfinance as yf
from bs4 import BeautifulSoup
import requests
import pandas as pd
from datetime import datetime, timedelta
from stock_universe import STOCK_UNIVERSE
import time
import random

class StockDataCollector:
    def __init__(self):
        self.stocks = STOCK_UNIVERSE
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }

    def get_market_indices(self):
        """Fetch last 5 days for NIFTY & SENSEX"""
        try:
            nifty = yf.Ticker("^NSEI").history(period="10d", interval="1d")
            sensex = yf.Ticker("^BSESN").history(period="10d", interval="1d")

            # Check if we have enough data
            if len(nifty) < 2 or len(sensex) < 2:
                print("Warning: Not enough index data")
                return None

            def summarize(df):
                cur = float(df["Close"].iloc[-1])
                prev = float(df["Close"].iloc[-2])
                ch = cur - prev
                ch_pct = ch / prev * 100
                return {
                    "current": round(cur, 2),
                    "prev_close": round(prev, 2),
                    "change": round(ch, 2),
                    "change_pct": round(ch_pct, 2),
                }

            return {"nifty": summarize(nifty), "sensex": summarize(sensex)}
        except Exception as e:
            print("Index fetch error:", e)
            return None

    def get_stock_data_with_retry(self, symbol: str, max_retries=3):
        """Fetch stock data with retry logic and delays"""
        for attempt in range(max_retries):
            try:
                # Random delay between 1-3 seconds to avoid rate limiting
                time.sleep(random.uniform(1.5, 3.0))
                
                today = datetime.now().date()
                start = today - timedelta(days=45)

                # Download data
                hist_daily = yf.download(
                    symbol, start=start, end=today + timedelta(days=1), 
                    interval="1d", progress=False, timeout=10
                )

                if hist_daily.empty or len(hist_daily) < 5:
                    print(f"  Skipping {symbol}: insufficient data")
                    return None

                # Get fundamentals
                ticker = yf.Ticker(symbol)
                info = ticker.info
                
                current_price = float(hist_daily["Close"].iloc[-1])
                month_return = (
                    (hist_daily["Close"].iloc[-1] - hist_daily["Close"].iloc[0])
                    / hist_daily["Close"].iloc[0]
                    * 100
                )
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
                if "429" in str(e) or "Too Many Requests" in str(e):
                    wait_time = (attempt + 1) * 5  # 5s, 10s, 15s
                    print(f"  Rate limited on {symbol}, waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"  Error {symbol}: {str(e)[:50]}")
                    return None
        
        print(f"  Failed {symbol} after {max_retries} retries")
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
        """Fetch data for stocks with rate limiting"""
        data = []
        total = len(self.stocks)
        
        for idx, sym in enumerate(self.stocks, 1):
            print(f"[{idx}/{total}] Fetching: {sym}")
            stock_data = self.get_stock_data_with_retry(sym)
            
            if stock_data:
                data.append(stock_data)
            
            # Extra delay every 10 stocks to be safe
            if idx % 10 == 0:
                print(f"  Progress checkpoint: {idx}/{total} done, pausing 5s...")
                time.sleep(5)
        
        print(f"\nSuccessfully fetched: {len(data)}/{total} stocks")
        return data

    def sector_performance(self, all_data):
        df = pd.DataFrame(all_data)
        if df.empty:
            return {}
        grp = df.groupby("sector")["month_return"].mean().sort_values(ascending=False)
        return grp.to_dict()
