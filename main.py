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
        print("No Telegram creds")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        requests.post(url, data={"chat_id": chat_id, "text": text})
    except Exception as e:
        print("Telegram text error:", e)


def send_telegram_pdf(path: str):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("No Telegram creds")
        return

    url = f"https://api.telegram.org/bot{token}/sendDocument"
    try:
        with open(path, "rb") as f:
            files = {"document": f}
            caption = (
                f"📊 Daily Stock Report\n"
                f"{datetime.now().strftime('%d %B %Y')}\n"
                f"Intraday + Portfolio (Medium Risk)"
            )
            data = {"chat_id": chat_id, "caption": caption}
            r = requests.post(url, data=data, files=files)
            print("Telegram status:", r.status_code, r.text[:200])
    except Exception as e:
        print("Telegram PDF error:", e)


def main():
    print("=" * 60)
    print("STOCK AGENT STARTED", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 60)

    send_telegram_message("🔄 Generating your daily stock market report...")

    collector = StockDataCollector()

    print("Fetching indices...")
    indices = collector.get_market_indices()

    print("Fetching stocks snapshot (may take a while)...")
    all_data = collector.get_all_stocks_snapshot()
    print("Total stocks with data:", len(all_data))

    print("Sector performance...")
    sector_perf = collector.sector_performance(all_data)

    print("Scraping news...")
    news = collector.scrape_market_news()

    analyzer = MarketAnalyzer()

    print("Building intraday analysis...")
    intraday = analyzer.analyze_intraday(indices, all_data, news, sector_perf)

    print("Building portfolio recommendations...")
    portfolio = analyzer.recommend_medium_risk(all_data)

    print("Generating PDF...")
    pdf_path = create_pdf(intraday, portfolio)

    print("Sending PDF via Telegram...")
    send_telegram_pdf(pdf_path)

    print("Done.")


if __name__ == "__main__":
    main()


