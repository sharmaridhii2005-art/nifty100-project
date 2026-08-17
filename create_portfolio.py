import sqlite3
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

db = sqlite3.connect("db/nifty100.db")

companies = db.execute(
    "SELECT COUNT(*) FROM companies"
).fetchone()[0]

sectors = db.execute(
    "SELECT COUNT(DISTINCT broad_sector) FROM sectors"
).fetchone()[0]

ratios = db.execute(
    "SELECT COUNT(*) FROM financial_ratios"
).fetchone()[0]

roe = db.execute(
    "SELECT AVG(return_on_equity_pct) "
    "FROM financial_ratios "
    "WHERE year = 'Mar 2024'"
).fetchone()[0]

margin = db.execute(
    "SELECT AVG(operating_profit_margin_pct) "
    "FROM financial_ratios "
    "WHERE year = 'Mar 2024'"
).fetchone()[0]

db.close()

output = Path("reports/portfolio/portfolio_summary.pdf")

styles = getSampleStyleSheet()

story = [
    Paragraph("NIFTY 100 PORTFOLIO SUMMARY", styles["Title"]),
    Spacer(1, 20),
    Paragraph(
        "Portfolio-level summary of the Nifty 100 analytics dataset.",
        styles["BodyText"],
    ),
    Spacer(1, 15),
]

table_data = [
    ["Metric", "Value"],
    ["Companies", str(companies)],
    ["Broad Sectors", str(sectors)],
    ["Financial Ratio Records", str(ratios)],
    ["Average ROE (Mar 2024)", f"{roe:.2f}%"],
    [
        "Average Operating Margin (Mar 2024)",
        f"{margin:.2f}%",
    ],
]

table = Table(
    table_data,
    colWidths=[260, 180],
)

table.setStyle(
    TableStyle(
        [
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("PADDING", (0, 0), (-1, -1), 8),
        ]
    )
)

story.append(table)

doc = SimpleDocTemplate(
    str(output),
    pagesize=A4,
    rightMargin=45,
    leftMargin=45,
    topMargin=45,
    bottomMargin=45,
)

doc.build(story)

print("Created:", output)
print("Size:", output.stat().st_size, "bytes")
