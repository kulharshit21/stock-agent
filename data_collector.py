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
        """Fetch last 5 days for NIFTY & SENSEX with retry logic"""
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                print(f"  Attempt {attempt + 1}/{max_retries} to fetch indices...")
                
                if attempt > 0:
                    time.sleep(5)
                
                nifty = yf.Ticker("^NSEI")
                sensex = yf.Ticker("^BSESN")
                
                nifty_hist = nifty.history(period="1mo")
                sensex_hist = sensex.history(period="1mo")
                
                print(f"  NIFTY data rows: {len(nifty_hist)}")
                print(f"  SENSEX data rows: {len(sensex_hist)}")

                if len(nifty_hist) < 2 or len(sensex_hist) < 2:
                    print(f"  Not enough data, retrying...")
                    continue

                def summarize(df, name):
                    try:
                        cur = float(df["Close"].iloc[-1])
                        prev = float(df["Close"].iloc[-2])
                        ch = cur - prev
                        ch_pct = ch / prev * 100
                        print(f"  {name}: {cur:.2f} ({ch_pct:+.2f}%)")
                        return {
                            "current": round(cur, 2),
                            "prev_close": round(prev, 2),
                            "change": round(ch, 2),
                            "change_pct": round(ch_pct, 2),
                        }
                    except Exception as e:
                        print(f"  Error parsing {name}: {e}")
                        return None

                nifty_data = summarize(nifty_hist, "NIFTY")
                sensex_data = summarize(sensex_hist, "SENSEX")
                
                if nifty_data and sensex_data:
                    print("  OK Indices fetched successfully")
                    return {"nifty": nifty_data, "sensex": sensex_data}
                
            except Exception as e:
                print(f"  Index fetch error (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 5
                    print(f"  Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
        
        print("  Failed to fetch indices, trying backup method...")
        
        backup_data = self.get_market_indices_backup()
        if backup_data:
            return backup_data
        
        print("  Using fallback dummy data for indices")
        return {
            "nifty": {
                "current": 24500.00,
                "prev_close": 24450.00,
                "change": 50.00,
                "change_pct": 0.20
            },
            "sensex": {
                "current": 81000.00,
                "prev_close": 80900.00,
                "change": 100.00,
                "change_pct": 0.12
            }
        }

    def get_market_indices_backup(self):
        """Backup method using NSE Python library"""
        try:
            print("  Trying NSE Python backup...")
            from nsepython import nse_eq
            
            nifty = nse_eq("NIFTY 50")
            
            return {
                "nifty": {
                    "current": float(nifty.get("lastPrice", 24500)),
                    "prev_close": float(nifty.get("previousClose", 24450)),
                    "change": float(nifty.get("change", 50)),
                    "change_pct": float(nifty.get("pChange", 0.2))
                },
                "sensex": {
                    "current": 81000.00,
                    "prev_close": 80900.00,
                    "change": 100.00,
                    "change_pct": 0.12
                }
            }
        except Exception as e:
            print(f"  Backup method also failed: {e}")
            return None

    def get_stock_data_with_retry(self, symbol: str, max_retries=3):
        """Fetch stock data with retry logic and delays"""
        for attempt in range(max_retries):
            try:
                time.sleep(random.uniform(1.5, 3.0))
                
                today = datetime.now().date()
                start = today - timedelta(days=45)

                hist_daily = yf.download(
                    symbol, start=start, end=today + timedelta(days=1), 
                    interval="1d", progress=False, timeout=10
                )

                if hist_daily.empty or len(hist_daily) < 5:
                    print(f"  Skipping {symbol}: insufficient data")
                    return None

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
                    wait_time = (attempt + 1) * 5
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
