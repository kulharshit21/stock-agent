import yfinance as yf
from bs4 import BeautifulSoup
import requests
import pandas as pd
from datetime import datetime, timedelta
from stock_universe import STOCK_UNIVERSE


class StockDataCollector:
    def __init__(self):
        self.stocks = STOCK_UNIVERSE
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }

    def get_market_indices(self):
        """Fetch last 5 days for NIFTY & SENSEX for intraday context."""
        try:
            nifty = yf.Ticker("^NSEI").history(period="5d", interval="1d")
            sensex = yf.Ticker("^BSESN").history(period="5d", interval="1d")

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

    def get_stock_ohlc_intraday(self, symbol: str):
        """
        Get current day's intraday OHLCV (5-min) and last 30 days EOD data.
        """
        try:
            today = datetime.now().date()
            start = today - timedelta(days=30)
            hist_daily = yf.download(
                symbol, start=start, end=today + timedelta(days=1), interval="1d", progress=False
            )
            intraday = yf.download(
                symbol, period="1d", interval="5m", progress=False
            )

            if hist_daily.empty:
                return None

            current_price = float(hist_daily["Close"].iloc[-1])
            month_return = (
                (hist_daily["Close"].iloc[-1] - hist_daily["Close"].iloc[0])
                / hist_daily["Close"].iloc[0]
                * 100
            )
            volatility = hist_daily["Close"].pct_change().std() * 100

            return {
                "symbol": symbol.replace(".NS", ""),
                "current_price": round(current_price, 2),
                "month_return": round(float(month_return), 2),
                "volatility": round(float(volatility), 2),
                "eod_history": hist_daily.tail(30),
                "intraday": intraday,
            }
        except Exception as e:
            print("Error intraday", symbol, e)
            return None

    def get_stock_fundamentals(self, symbol: str):
        """Use yfinance .info for PE, beta, dividend etc."""
        try:
            t = yf.Ticker(symbol)
            info = t.info
            return {
                "symbol": symbol.replace(".NS", ""),
                "name": info.get("shortName", symbol),
                "sector": info.get("sector", "N/A"),
                "pe_ratio": float(info.get("trailingPE") or 0),
                "pb_ratio": float(info.get("priceToBook") or 0),
                "market_cap": int(info.get("marketCap") or 0),
                "beta": float(info.get("beta") or 1),
                "dividend_yield": float(info.get("dividendYield") or 0) * 100,
                "week52_high": float(info.get("fiftyTwoWeekHigh") or 0),
                "week52_low": float(info.get("fiftyTwoWeekLow") or 0),
            }
        except Exception as e:
            print("Fundamentals error", symbol, e)
            return None

    def scrape_market_news(self, limit: int = 12):
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
                print("News error", e)
        # dedupe and limit
        return list(dict.fromkeys(news))[:limit]

    def get_all_stocks_snapshot(self):
        """Return merged fundamentals + 30D + intraday meta for ALL stocks."""
        data = []
        for sym in self.stocks:
            print("Fetching:", sym)
            f = self.get_stock_fundamentals(sym)
            o = self.get_stock_ohlc_intraday(sym)
            if not f or not o:
                continue
            row = {**f, **{k: o[k] for k in ["current_price", "month_return", "volatility"]}}
            data.append(row)
        return data

    def sector_performance(self, all_data):
        df = pd.DataFrame(all_data)
        if df.empty:
            return {}
        grp = df.groupby("sector")["month_return"].mean().sort_values(ascending=False)
        return grp.to_dict()


