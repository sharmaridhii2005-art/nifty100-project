from src.screener.engine import ScreenerEngine
from src.screener.presets import *
from src.screener.exporter import export_screeners

engine = ScreenerEngine()

results = {
    "Quality Compounder": engine.run(QUALITY_COMPOUNDER),
    "Value Pick": engine.run(VALUE_PICK),
    "Growth Accelerator": engine.run(GROWTH_ACCELERATOR),
    "Dividend Champion": engine.run(DIVIDEND_CHAMPION),
    "Debt Free Blue Chip": engine.run(DEBT_FREE_BLUE_CHIP),
    "Turnaround Watch": engine.run(TURNAROUND_WATCH),
}

export_screeners(results)