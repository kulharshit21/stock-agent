from datetime import datetime


class MarketAnalyzer:
    def analyze_intraday(self, indices, stocks_data, news, sector_perf):
        lines = []

        lines.append("=" * 70)
        lines.append("INTRADAY MARKET OVERVIEW")
        lines.append("=" * 70)
        lines.append(f"Date: {datetime.now().strftime('%d %B %Y, %A')}\n")

        if indices:
            n = indices["nifty"]
            s = indices["sensex"]

            avg = (n["change_pct"] + s["change_pct"]) / 2
            n_trend = "BULLISH" if n["change"] > 0 else "BEARISH"
            s_trend = "BULLISH" if s["change"] > 0 else "BEARISH"

            lines.append(
                f"NIFTY 50: {n['current']} ({n['change']:+.2f}, {n['change_pct']:+.2f}%) [{n_trend}]"
            )
            lines.append(
                f"SENSEX : {s['current']} ({s['change']:+.2f}, {s['change_pct']:+.2f}%) [{s_trend}]"
            )

            if avg > 1:
                mood = "Strong risk-on sentiment, buyers in control."
            elif avg > 0:
                mood = "Mild positive bias, dips likely to be bought."
            elif avg > -1:
                mood = "Cautious, range-bound to mildly negative tone."
            else:
                mood = "Risk-off sentiment, aggressive selling pressure."

            lines.append(f"\nOverall Market Mood: {mood}\n")

        lines.append("=" * 70)
        lines.append("TOP GAINERS / LOSERS (Last 30 Days)")
        lines.append("=" * 70)

        sorted_stocks = sorted(stocks_data, key=lambda x: x["month_return"], reverse=True)
        gainers = sorted_stocks[:10]
        losers = sorted_stocks[-10:]

        lines.append("\nTop 10 Gainers:")
        for s in gainers:
            lines.append(
                f"  {s['symbol']:>8}  ₹{s['current_price']:>8.2f}  ({s['month_return']:+6.2f}%)  Sector: {s['sector']}"
            )

        lines.append("\nTop 10 Losers:")
        for s in losers:
            lines.append(
                f"  {s['symbol']:>8}  ₹{s['current_price']:>8.2f}  ({s['month_return']:+6.2f}%)  Sector: {s['sector']}"
            )

        lines.append("\n" + "=" * 70)
        lines.append("SECTOR PERFORMANCE (Last 30 Days)")
        lines.append("=" * 70)

        for sector, ret in list(sector_perf.items())[:12]:
            emoji = "▲" if ret > 0 else "▼"
            lines.append(f"  {sector:25} {emoji} {ret:+6.2f}%")

        lines.append("\n" + "=" * 70)
        lines.append("KEY MARKET NEWS (Headlines)")
        lines.append("=" * 70)
        for i, h in enumerate(news[:8], 1):
            lines.append(f"{i:2d}. {h}")

        # strategy
        lines.append("\n" + "=" * 70)
        lines.append("TRADING GOALS & INTRADAY STRATEGY")
        lines.append("=" * 70)

        if indices:
            avg = (indices["nifty"]["change_pct"] + indices["sensex"]["change_pct"]) / 2
            if avg >= 0:
                lines.append(
                    "• Bias: Mild to strong bullish. Prefer buying quality names on intraday dips."
                )
                lines.append(
                    "• Focus: Sectors at top of performance table; avoid illiquid small-caps."
                )
                lines.append("• Position sizing: 2–3% of capital per trade with strict stop losses.")
            else:
                lines.append("• Bias: Defensive. Capital protection is priority.")
                lines.append(
                    "• Focus: Large-cap, low beta names; avoid leveraged or speculative counters."
                )
                lines.append(
                    "• Position sizing: 1–2% per trade, tighter stop losses, partial profit booking."
                )

        return "\n".join(lines)

    def recommend_medium_risk(self, stocks_data):
        lines = []

        lines.append("=" * 70)
        lines.append("MEDIUM-RISK PORTFOLIO STOCKS")
        lines.append("=" * 70)

        filtered = []
        for s in stocks_data:
            beta = s["beta"]
            pe = s["pe_ratio"]
            dy = s["dividend_yield"]
            vol = s["volatility"]

            risk = 5
            if beta < 0.8:
                risk -= 1
            elif beta > 1.2:
                risk += 1

            if 0 < pe < 25:
                risk -= 1
            elif pe > 40:
                risk += 1

            if dy > 1:
                risk -= 1

            if vol < 2:
                risk -= 1
            elif vol > 4:
                risk += 1

            if 3 <= risk <= 7:  # medium risk
                s_copy = dict(s)
                s_copy["risk_score"] = risk
                filtered.append(s_copy)

        filtered.sort(key=lambda x: (x["risk_score"], -x["month_return"]))

        lines.append("Selection rules:")
        lines.append("  • Beta roughly between 0.8 and 1.3")
        lines.append("  • PE not extremely high (> 40 avoided)")
        lines.append("  • Some preference for dividend payers")
        lines.append("  • Moderate volatility; not extreme movers\n")

        top = filtered[:12]
        for i, s in enumerate(top, 1):
            cp = s["current_price"]
            entry = cp
            sl = round(cp * 0.95, 2)
            t1 = round(cp * 1.08, 2)
            t2 = round(cp * 1.15, 2)

            lines.append("-" * 70)
            lines.append(f"#{i}  {s['symbol']}  ({s['name'][:30]})")
            lines.append(f"Sector        : {s['sector']}")
            lines.append(f"Risk Score    : {s['risk_score']}/10")
            lines.append(f"Price         : ₹{cp:.2f}")
            lines.append(f"1M Return     : {s['month_return']:+.2f}%")
            lines.append(f"PE / Beta     : {s['pe_ratio']:.2f} / {s['beta']:.2f}")
            lines.append(f"Dividend Yield: {s['dividend_yield']:.2f}%")
            lines.append(f"Volatility    : {s['volatility']:.2f}% (30D)")
            lines.append(f"ENTRY   : ₹{entry:.2f}")
            lines.append(f"STOPLOSS: ₹{sl:.2f}  (~5% downside)")
            lines.append(f"TARGET1: ₹{t1:.2f}  (~8% upside)")
            lines.append(f"TARGET2: ₹{t2:.2f}  (~15% upside)\n")

        lines.append("=" * 70)
        lines.append("SUGGESTED ALLOCATION (MEDIUM RISK)")
        lines.append("=" * 70)
        lines.append("• 40% Large caps (stable compounders).")
        lines.append("• 35% Quality midcaps with earnings visibility.")
        lines.append("• 25% sector leaders or structural themes.")
        lines.append("\nRisk rules:")
        lines.append("• Max 10% of capital in any single stock.")
        lines.append("• Always use stop loss; review weekly; rebalance quarterly.\n")
        lines.append("=" * 70)
        lines.append("DISCLAIMER")
        lines.append("=" * 70)
        lines.append(
            "This report is for educational purposes only and is NOT investment advice. "
            "Markets are risky; do your own research or consult a SEBI-registered advisor."
        )

        return "\n".join(lines)

