from fpdf import FPDF
from datetime import datetime


class StockReportPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)

    def header(self):
        self.set_font("Helvetica", "B", 15)
        self.cell(0, 10, "DAILY INDIAN STOCK MARKET REPORT", 0, 1, "C")
        self.set_font("Helvetica", "", 10)
        self.cell(0, 6, datetime.now().strftime("%A, %d %B %Y"), 0, 1, "C")
        self.ln(3)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.cell(
            0,
            10,
            f"Page {self.page_no()}/4 • Generated automatically",
            0,
            0,
            "C",
        )

    def title_block(self, title: str):
        self.set_font("Helvetica", "B", 13)
        self.set_fill_color(230, 230, 230)
        self.cell(0, 9, title, 0, 1, "L", True)
        self.ln(2)

    def body_text(self, text: str):
        self.set_font("Helvetica", "", 9)
        safe = text.encode("latin-1", "replace").decode("latin-1")
        self.multi_cell(0, 4.5, safe)
        self.ln(2)


def create_pdf(intraday_text: str, portfolio_text: str) -> str:
    pdf = StockReportPDF()

    intraday_lines = intraday_text.split("\n")
    portfolio_lines = portfolio_text.split("\n")

    mid1 = len(intraday_lines) // 2
    mid2 = len(portfolio_lines) // 2

    # Page 1
    pdf.add_page()
    pdf.title_block("PART 1 • INTRADAY MARKET CONTEXT & SENTIMENT")
    pdf.body_text("\n".join(intraday_lines[:mid1]))

    # Page 2
    pdf.add_page()
    pdf.title_block("PART 2 • STRATEGY, GOALS & SECTOR VIEW")
    pdf.body_text("\n".join(intraday_lines[mid1:]))

    # Page 3
    pdf.add_page()
    pdf.title_block("PART 3 • MEDIUM-RISK STOCK SHORTLIST")
    pdf.body_text("\n".join(portfolio_lines[:mid2]))

    # Page 4
    pdf.add_page()
    pdf.title_block("PART 4 • DETAILED LEVELS & PORTFOLIO PLAN")
    pdf.body_text("\n".join(portfolio_lines[mid2:]))

    filename = f"stock_report_{datetime.now().strftime('%Y%m%d')}.pdf"
    pdf.output(filename)
    return filename


