import glob
import os

import numpy as np
import pandas as pd


DATA_DIRS = [
    ("./data_kospi", "KOSPI"),
    ("./data_kosdaq", "KOSDAQ"),
]

INVESTOR_COLUMNS = {
    "Retail": ("Retail_Buy_Volume", "Retail_Sell_Volume"),
    "Institution": ("Institution_Buy_Volume", "Institution_Sell_Volume"),
    "Foreign": ("Foreign_Buy_Volume", "Foreign_Sell_Volume"),
}


def add_trading_proportion_columns(df: pd.DataFrame) -> pd.DataFrame:
    total_buy = pd.to_numeric(df.get("Total_Buy_Volume", 0), errors="coerce").fillna(0)
    total_sell = pd.to_numeric(df.get("Total_Sell_Volume", 0), errors="coerce").fillna(0)
    total_volume = (total_buy + total_sell).astype(float)

    for investor_name, (buy_col, sell_col) in INVESTOR_COLUMNS.items():
        buy_volume = pd.to_numeric(df.get(buy_col, 0), errors="coerce").fillna(0)
        sell_volume = pd.to_numeric(df.get(sell_col, 0), errors="coerce").fillna(0)
        investor_volume = (buy_volume + sell_volume).astype(float)

        proportion = np.divide(
            investor_volume,
            total_volume,
            out=np.zeros_like(investor_volume, dtype=float),
            where=total_volume != 0,
        )
        df[f"{investor_name}_Trading_Proportion"] = proportion

    return df


def safe_read_excel(file_path: str) -> pd.DataFrame:
    return pd.read_excel(file_path, engine="openpyxl")


def process_directory(directory: str, market_name: str) -> None:
    excel_files = sorted(
        glob.glob(os.path.join(directory, "*.xlsx")),
        key=lambda x: os.path.basename(x),
    )

    processed = 0
    skipped = 0
    for file_path in excel_files:
        if os.path.basename(file_path).startswith("~$"):
            continue

        try:
            df = safe_read_excel(file_path)
            df = add_trading_proportion_columns(df)
            df = df.replace([np.inf, -np.inf], np.nan).fillna(0.0)
            with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
                df.to_excel(writer, index=False)
            processed += 1
        except Exception as exc:
            skipped += 1
            print(f"[{market_name}] skipped {os.path.basename(file_path)}: {type(exc).__name__}: {exc}")

    print(f"[{market_name}] {processed} files updated, {skipped} skipped")


def main() -> None:
    for directory, market_name in DATA_DIRS:
        process_directory(directory, market_name)


if __name__ == "__main__":
    main()
