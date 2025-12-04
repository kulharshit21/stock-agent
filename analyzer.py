from datetime import datetime

class MarketAnalyzer:
    def analyze_intraday(self, indices, stocks_data, news, sector_perf):
        lines = []
        lines.append("=" * 70)
        lines.append("INTRADAY MARKET ANALYSIS - REAL DATA")
        lines.append("=" * 70)
        lines.append(f"Generated: {datetime.now().strftime('%d %B %Y, %H:%M IST')}\n")

        if indices:
            n = indices["nifty"]
            s = indices["sensex"]
            avg_change = (n["change_pct"] + s["change_pct"]) / 2
            
            lines.append(f"NIFTY 50  : {n['current']:>9.2f} ({n['change']:+7.2f}) [{n['change_pct']:+6.2f}%]")
            lines.append(f"SENSEX    : {s['current']:>9.2f} ({s['change']:+7.2f}) [{s['change_pct']:+6.2f}%]\n")
            
            if avg_change > 1:
                mood = "STRONG BULLISH - Risk-on, buyers dominant"
            elif avg_change > 0:
                mood = "MILD BULLISH - Positive bias, buying on dips"
            elif avg_change > -1:
                mood = "MILD BEARISH - Cautious, range-bound"
            else:
                mood = "STRONG BEARISH - Risk-off, selling pressure"
            
            lines.append(f"Market Sentiment: {mood}\n")
        else:
            lines.append("Market indices unavailable - analyzing stocks directly\n")

        if stocks_data:
            sorted_stocks = sorted(stocks_data, key=lambda x: x["month_return"], reverse=True)
            
            lines.append("=" * 70)
            lines.append("TOP 15 GAINERS (Last 30 Days - REAL DATA)")
            lines.append("=" * 70)
            for i, s in enumerate(sorted_stocks[:15], 1):
                lines.append(
                    f"{i:2d}. {s['symbol']:>10} Rs{s['current_price']:>8.2f} "
                    f"({s['month_return']:+6.2f}%) | {s['sector']}"
                )

            lines.append("\n" + "=" * 70)
            lines.append("TOP 15 LOSERS (Last 30 Days - REAL DATA)")
            lines.append("=" * 70)
            for i, s in enumerate(sorted_stocks[-15:], 1):
                lines.append(
                    f"{i:2d}. {s['symbol']:>10} Rs{s['current_price']:>8.2f} "
                    f"({s['month_return']:+6.2f}%) | {s['sector']}"
                )

        if sector_perf:
            lines.append("\n" + "=" * 70)
            lines.append("SECTOR PERFORMANCE (Last 30 Days)")
            lines.append("=" * 70)
            for sector, ret in list(sector_perf.items())[:15]:
                emoji = "▲" if ret > 0 else "▼"
                lines.append(f"{emoji} {sector:25} {ret:+7.2f}%")

        if news:
            lines.append("\n" + "=" * 70)
            lines.append("LATEST MARKET NEWS")
            lines.append("=" * 70)
            for i, headline in enumerate(news[:8], 1):
                truncated = headline[:65] + "..." if len(headline) > 65 else headline
                lines.append(f"{i}. {truncated}")

        lines.append("\n" + "=" * 70)
        lines.append("INTRADAY TRADING STRATEGY")
        lines.append("=" * 70)
        
        if indices:
            avg = (indices["nifty"]["change_pct"] + indices["sensex"]["change_pct"]) / 2
            if avg >= 0.5:
                strategy = "BIAS: BULLISH\n• Prefer buying quality names on dips\n• Focus on top gaining sectors\n• Use 2-3% position size per trade\n• Tight stop losses below support"
            elif avg >= -0.5:
                strategy = "BIAS: NEUTRAL/RANGE-BOUND\n• Trade within key support/resistance\n• Avoid large directional bets\n• Focus on volatile individual stocks\n• Use 1-2% per trade, take profits early"
            else:
                strategy = "BIAS: BEARISH\n• Defensive approach, protect capital\n• Avoid leveraged/speculative trades\n• Focus on large-cap dividend payers\n• Use tight stops, smaller position sizes"
            lines.append(strategy)
        
        return "\n".join(lines)

    def recommend_medium_risk(self, stocks_data):
        lines = []
        lines.append("=" * 70)
        lines.append("MEDIUM-RISK PORTFOLIO - REAL STOCK ANALYSIS")
        lines.append("=" * 70)

        if not stocks_data:
            lines.append("No stock data available")
            return "\n".join(lines)

        filtered = []
        for s in stocks_data:
            beta = s["beta"]
            pe = s["pe_ratio"]
            dy = s["dividend_yield"]
            vol = s["volatility"]

            risk = 5
            if beta < 0.8:
                risk -= 1
            elif beta > 1.3:
                risk += 1
            if 15 < pe < 30:
                risk -= 1
            elif pe > 40:
                risk += 1
            if dy > 1.5:
                risk -= 1
            if vol < 2:
                risk -= 1
            elif vol > 4:
                risk += 1

            if 3 <= risk <= 7:
                s_copy = dict(s)
                s_copy["risk_score"] = risk
                filtered.append(s_copy)

        if not filtered:
            lines.append("No medium-risk stocks found")
            return "\n".join(lines)

        filtered.sort(key=lambda x: (x["risk_score"], -x["month_return"]))

        lines.append(f"\nFound {len(filtered)} medium-risk stocks\n")

        for i, s in enumerate(filtered[:12], 1):
            cp = s["current_price"]
            entry = cp
            sl = round(cp * 0.95, 2)
            t1 = round(cp * 1.08, 2)
            t2 = round(cp * 1.15, 2)
            
            lines.append("-" * 70)
            lines.append(f"#{i:2d} {s['symbol']:>10} | {s['name'][:40]}")
            lines.append("-" * 70)
            lines.append(f"Sector         : {s['sector']}")
            lines.append(f"Risk Score     : {s['risk_score']}/10")
            lines.append(f"Price          : Rs{cp:.2f}")
            lines.append(f"30D Return     : {s['month_return']:+.2f}%")
            lines.append(f"PE / Beta      : {s['pe_ratio']:.2f} / {s['beta']:.2f}")
            lines.append(f"Dividend Yield : {s['dividend_yield']:.2f}%")
            lines.append(f"52W High/Low   : Rs{s['week52_high']:.2f} / Rs{s['week52_low']:.2f}")
            lines.append(f"\n  ENTRY      : Rs{entry:.2f}")
            lines.append(f"  STOPLOSS   : Rs{sl:.2f}  (5% downside)")
            lines.append(f"  TARGET1    : Rs{t1:.2f}  (8% upside)")
            lines.append(f"  TARGET2    : Rs{t2:.2f}  (15% upside)\n")

        lines.append("=" * 70)
        lines.append("DISCLAIMER")
        lines.append("=" * 70)
        lines.append("This is for EDUCATIONAL purposes only. NOT investment advice.")

        return "\n".join(lines)
