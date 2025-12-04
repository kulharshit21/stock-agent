import os
from datetime import datetime
import requests

from data_collector import StockDataCollector
from analyzer import MarketAnalyzer
from report_generator import create_pdf

def send_telegram_message(text: str):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("Telegram credentials missing")
        return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        requests.post(url, data={"chat_id": chat_id, "text": text}, timeout=10)
    except Exception as e:
        print(f"Telegram error: {e}")

def send_telegram_pdf(path: str):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("Telegram credentials missing")
        return
    url = f"https://api.telegram.org/bot{token}/sendDocument"
    try:
        with open(path, "rb") as f:
            files = {"document": f}
            caption = (
                f"DAILY STOCK REPORT\n"
                f"{datetime.now().strftime('%d %B %Y')}\n\n"
                f"Intraday Analysis + Medium-Risk Stocks"
            )
            data = {"chat_id": chat_id, "caption": caption}
            r = requests.post(url, data=data, files=files, timeout=30)
            print(f"PDF sent: {r.status_code}")
    except Exception as e:
        print(f"PDF error: {e}")

def main():
    print("=" * 60)
    print("STOCK AGENT STARTED", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 60)

    send_telegram_message("Starting daily stock report generation...")

    collector = StockDataCollector()

    print("\nStep 1: Fetching market indices...")
    indices = collector.get_market_indices_real_only()

    print("\nStep 2: Fetching ALL stock data (real data only)...")
    send_telegram_message("Fetching data for 150+ stocks. This may take 10-15 minutes...")
    all_data = collector.get_all_stocks_real_data()

    if len(all_data) < 20:
        msg = f"FAILED: Only {len(all_data)} stocks fetched. Aborting."
        print(msg)
        send_telegram_message(msg)
        return

    print(f"\nStep 3: Analyzing sectors...")
    sector_perf = collector.sector_performance(all_data)

    print("\nStep 4: Scraping news...")
    news = collector.scrape_market_news()

    analyzer = MarketAnalyzer()
    print("\nStep 5: Building intraday analysis...")
    intraday = analyzer.analyze_intraday(indices, all_data, news, sector_perf)

    print("\nStep 6: Building portfolio recommendations...")
    portfolio = analyzer.recommend_medium_risk(all_data)

    print("\nStep 7: Generating PDF...")
    pdf_path = create_pdf(intraday, portfolio)

    print("\nStep 8: Sending PDF via Telegram...")
    send_telegram_pdf(pdf_path)
    send_telegram_message(f"✅ Report complete! Analyzed {len(all_data)} verified stocks.")

    print("\n✅ Done!")

if __name__ == "__main__":
    main()
