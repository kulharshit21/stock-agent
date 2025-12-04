def main():
    print("=" * 60)
    print("STOCK AGENT STARTED", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 60)

    send_telegram_message("🔄 Starting stock report generation...")

    collector = StockDataCollector()

    print("\n📊 Step 1: Fetching market indices...")
    indices = collector.get_market_indices()
    if not indices:
        send_telegram_message("❌ Failed to fetch market indices. Will retry next run.")
        return

    print("\n📈 Step 2: Fetching stocks data (this will take 10-15 mins)...")
    send_telegram_message("⏳ Fetching data for 150+ stocks, please wait 10-15 minutes...")
    
    all_data = collector.get_all_stocks_snapshot()
    
    if len(all_data) < 20:
        send_telegram_message(f"❌ Only {len(all_data)} stocks fetched. Aborting.")
        return
    
    print(f"✅ Total stocks with data: {len(all_data)}")

    print("\n🔍 Step 3: Analyzing sectors...")
    sector_perf = collector.sector_performance(all_data)

    print("\n📰 Step 4: Scraping news...")
    news = collector.scrape_market_news()

    analyzer = MarketAnalyzer()
    print("\n📝 Step 5: Building intraday analysis...")
    intraday = analyzer.analyze_intraday(indices, all_data, news, sector_perf)

    print("\n💼 Step 6: Building portfolio recommendations...")
    portfolio = analyzer.recommend_medium_risk(all_data)

    print("\n📄 Step 7: Generating PDF...")
    pdf_path = create_pdf(intraday, portfolio)

    print("\n📤 Step 8: Sending PDF via Telegram...")
    send_telegram_pdf(pdf_path)
    send_telegram_message(f"✅ Report complete! Analyzed {len(all_data)} stocks.")

    print("\n✅ Done!")

if __name__ == "__main__":
    main()
