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
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

    def get_market_indices_real_only(self):
        """
        REAL DATA ONLY - No fallback, no dummy data.
        If indices fail, we skip them but continue with stock analysis.
        """
        try:
            print("Fetching real NIFTY & SENSEX data...")
            time.sleep(2)
            
            nifty = yf.Ticker("^NSEI")
            sensex = yf.Ticker("^BSESN")
            
            nifty_hist = nifty.history(period="30d")
            sensex_hist = sensex.history(period="30d")
            
            if len(nifty_hist) < 2 or len(sensex_hist) < 2:
                print("Warning: Insufficient index data - continuing without indices")
                return None

            def summarize(df):
                cur = float(df["Close"].iloc[-1])
                prev = float(df["Close"].iloc[-2])
                ch = cur - prev
                ch_pct = (ch / prev * 100) if prev != 0 else 0
                return {
                    "current": round(cur, 2),
                    "prev_close": round(prev, 2),
                    "change": round(ch, 2),
                    "change_pct": round(ch_pct, 2),
                }

            nifty_data = summarize(nifty_hist)
            sensex_data = summarize(sensex_hist)
            
            print(f"NIFTY: {nifty_data['current']} ({nifty_data['change_pct']:+.2f}%)")
            print(f"SENSEX: {sensex_data['current']} ({sensex_data['change_pct']:+.2f}%)")
            
            return {"nifty": nifty_data, "sensex": sensex_data}
            
        except Exception as e:
            print(f"Index fetch failed: {e}")
            print("Will continue with stock analysis only")
            return None

    def get_stock_data_verified(self, symbol: str):
        """
        Fetch REAL stock data only. Skip if any data is missing or corrupted.
        No retry, no fallback - either we get real data or skip.
        """
        try:
            time.sleep(random.uniform(1, 2))
            
            today = datetime.now().date()
            start = today - timedelta(days=60)
            
            hist = yf.download(
                symbol, start=start, end=today + timedelta(days=1),
                interval="1d", progress=False, timeout=15
            )
            
            if hist.empty or len(hist) < 20:
                return None
            
            if hist["Close"].isnull().any():
                return None
            
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            current_price = float(hist["Close"].iloc[-1])
            if current_price <= 0:
                return None
            
            month_return = (
                (hist["Close"].iloc[-1] - hist["Close"].iloc[0])
                / hist["Close"].iloc[0] * 100
            )
            
            volatility = hist["Close"].pct_change().std() * 100
            
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
            return None

    def get_all_stocks_real_data(self):
        """Fetch ONLY stocks with verified real data"""
        data = []
        failed = []
        total = len(self.stocks)
        
        for idx, sym in enumerate(self.stocks, 1):
            stock_data = self.get_stock_data_verified(sym)
            
            if stock_data:
                data.append(stock_data)
                print(f"[{idx}/{total}] OK {sym:15} Rs {stock_data['current_price']:>8.2f}")
            else:
                failed.append(sym)
                print(f"[{idx}/{total}] XX {sym:15} (skip)")
            
            if idx % 15 == 0:
                print(f"    Checkpoint: {idx}/{total}, wait 3s...")
                time.sleep(3)
        
        print(f"\nResults: {len(data)} stocks OK, {len(failed)} skipped")
        print(f"Success: {len(data)/total*100:.1f}%")
        
        return data

    def scrape_market_news(self, limit: int = 10):
        """Scrape REAL market news"""
        news = []
        urls = [
            "https://economictimes.indiatimes.com/markets/stocks/news",
            "https://www.moneycontrol.com/news/business/markets/",
        ]
        
        for url in urls:
            try:
                r = requests.get(url, headers=self.headers, timeout=10)
                soup = BeautifulSoup(r.text, "lxml")
                for h in soup.find_all(["h2", "h3"], limit=limit):
                    text = h.get_text(strip=True)
                    if text and len(text) > 20:
                        news.append(text)
            except:
                pass
        
        return list(dict.fromkeys(news))[:limit]

    def sector_performance(self, all_data):
        """Calculate REAL sector performance from actual stock data"""
        if not all_data:
            return {}
        df = pd.DataFrame(all_data)
        grp = df.groupby("sector")["month_return"].mean().sort_values(ascending=False)
        return grp.to_dict()
