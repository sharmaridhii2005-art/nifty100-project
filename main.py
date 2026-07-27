import argparse
import os
import pandas as pd

from src.screener.engine import ScreenerEngine
from src.screener.presets import *

PRESETS = {
    "quality": QUALITY_COMPOUNDER,
    "value": VALUE_PICK,
    "growth": GROWTH_ACCELERATOR,
    "dividend": DIVIDEND_CHAMPION,
    "debtfree": DEBT_FREE_BLUE_CHIP,
    "turnaround": TURNAROUND_WATCH,
}



engine = ScreenerEngine()

import os

os.makedirs("output", exist_ok=True)

with pd.ExcelWriter(
    "output/screener_output.xlsx",
    engine="openpyxl"
) as writer:

    for preset_name, preset in PRESETS.items():

        print(f"\nRunning {preset_name} preset...")

        df = engine.run(preset)

        display_columns = [
            "company_id",
            "year_x",
            "broad_sector",
            "sub_sector",
            "return_on_equity_pct",
            "net_profit_margin_pct",
            "debt_to_equity",
            "pe_ratio",
            "pb_ratio",
            "market_cap_crore",
            "dividend_yield_pct",
            "composite_quality_score"
        ]

        df = df[display_columns]

        df.to_excel(
            writer,
            sheet_name=preset_name[:31],
            index=False
        )

        print(df.head(10))

print("\nGenerated:")
print("output/screener_output.xlsx")