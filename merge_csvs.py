import re
from pathlib import Path
import pandas as pd

EXTRACTED_DIR = Path("extracted")
OUTPUT_CSV = Path("doe_north_luzon_prices.csv")
KEY_COLS = ["North Luzon", "Province", "City", "Product"]

REGION_ORDER = [
    "Cordillera Administrative Region (CAR)",
    "Ilocos Region (REGION I)",
    "Cagayan Valley (REGION II)",
    "Central Luzon (REGION III)",
]

PRODUCT_ORDER = [
    "RON 100",
    "RON 97",
    "RON 95",
    "RON 91",
    "DIESEL",
    "DIESEL PLUS",
    "KEROSENE",
]

MONTH_MAP = {
    "JAN": 1, "JANUARY": 1,
    "FEB": 2, "FEBRUARY": 2,
    "MAR": 3, "MARCH": 3,
    "APR": 4, "APRIL": 4,
    "MAY": 5,
    "JUN": 6, "JUNE": 6,
    "JUL": 7, "JULY": 7,
    "AUG": 8, "AUGUST": 8,
    "SEP": 9, "SEPT": 9, "SEPTEMBER": 9,
    "OCT": 10, "OCTOBER": 10,
    "NOV": 11, "NOVEMBER": 11,
    "DEC": 12, "DECEMBER": 12,
}


def week_sort_key(col_name):
    upper = col_name.upper()
    year_match = re.search(r"\b(20\d{2})\b", upper)
    year = int(year_match.group(1)) if year_match else 9999

    month = 99
    for token in re.findall(r"[A-Z]+", upper):
        if token in MONTH_MAP:
            month = MONTH_MAP[token]
            break

    day_match = re.search(r"\b(\d{1,2})\b", upper)
    day = int(day_match.group(1)) if day_match else 99

    return (year, month, day, col_name)


def sort_master_df(df):
    region_rank = {r: i for i, r in enumerate(REGION_ORDER)}
    product_rank = {p: i for i, p in enumerate(PRODUCT_ORDER)}

    df = df.copy()
    df["_r"] = df["North Luzon"].map(lambda x: region_rank.get(x, 999))
    df["_p"] = df["Product"].map(lambda x: product_rank.get(x, 999))
    df = df.sort_values(
        by=["_r", "North Luzon", "Province", "City", "_p"],
        kind="stable",
    )
    return df.drop(columns=["_r", "_p"]).reset_index(drop=True)


csv_files = sorted(EXTRACTED_DIR.glob("*.csv"))
if not csv_files:
    raise SystemExit(f"No CSV files found in {EXTRACTED_DIR}")

master_df = pd.DataFrame(columns=KEY_COLS)

for csv_path in csv_files:
    df = pd.read_csv(csv_path, dtype=str)
    for col in KEY_COLS:
        if col in df.columns:
            df[col] = df[col].fillna("").str.strip()

    week_cols = [c for c in df.columns if c not in KEY_COLS]
    if not week_cols:
        continue

    df = df.drop_duplicates(subset=KEY_COLS, keep="first")

    overlap = [c for c in week_cols if c in master_df.columns]
    if overlap:
        master_df = master_df.drop(columns=overlap)

    master_df = pd.merge(master_df, df[KEY_COLS + week_cols], on=KEY_COLS, how="outer")
    print(f"Merged {csv_path.name} ({len(df)} rows)")

all_week_cols = sorted(
    [c for c in master_df.columns if c not in KEY_COLS],
    key=week_sort_key,
)
master_df = master_df[KEY_COLS + all_week_cols]
master_df = sort_master_df(master_df)
master_df = master_df.fillna("-")

master_df.to_csv(OUTPUT_CSV, index=False)
print(f"Saved {OUTPUT_CSV} ({len(master_df)} rows, {len(all_week_cols)} weeks)")