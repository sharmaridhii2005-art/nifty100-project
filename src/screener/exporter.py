import pandas as pd


def export_screeners(results, output_file="output/screener_output.xlsx"):

    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:

        for sheet_name, df in results.items():

            df.to_excel(
                writer,
                sheet_name=sheet_name[:31],   # Excel sheet name limit
                index=False
            )

    print(f"Saved: {output_file}")