# DOE North Luzon Liquid Fuel Price Monitoring Scraper

Extracts weekly common fuel prices (`RON 100`, `RON 97`, `RON 95`, `RON 91`, `DIESEL`, `DIESEL PLUS`, `KEROSENE`) from Department of Energy (DOE) North Luzon liquid fuel price monitoring PDFs, saves per-week CSVs, and merges them into a single master CSV sorted by region, province, city, and product.

## Libraries to Install

* **`pdfplumber`** — Extracts positioned words and layout coordinates from text-based PDF pages.
* **`pymupdf` (`fitz`)** — Provides a secondary text-layer fallback and renders image-only/scanned PDF pages to images for OCR.
* **`rapidocr-onnxruntime`** — Runs local OCR fallback on pages that have no selectable text layer (no separate Tesseract binary installation required).
* **`pandas`** — Cleans, outer-merges weekly tables, sorts rows/columns, and exports CSV files.

Install all required libraries with:

```bash
python -m pip install -r requirements.txt
```

## Project Structure

```text
.
├── extract_pdfs.py      # Extracts each weekly PDF into extracted/<week>.csv
├── merge_csvs.py        # Merges all CSVs in extracted/ into doe_north_luzon_prices.csv
├── requirements.txt     # Python package dependencies
├── .gitignore           # Excludes local PDFs, generated CSVs, and cache folders
├── README.md
└── pdfs/                # Place weekly DOE PDFs here (create if not present)
```

## How to Run

1. **Add PDFs:** Create a `pdfs/` folder in the project directory and place the DOE weekly PDF reports inside it.
2. **Extract each PDF to its own CSV:**
   ```bash
   python extract_pdfs.py
   ```
   Output files are written to `extracted/`. Set `SKIP_EXISTING = False` inside `extract_pdfs.py` if you want to re-extract files already in `extracted/`.
3. **Combine all extracted weeks into one sheet:**
   ```bash
   python merge_csvs.py
   ```
   This writes the combined output to `doe_north_luzon_prices.csv`, adding a new column for each week and new rows for any newly appearing provinces or cities.

## Notes

* Close `doe_north_luzon_prices.csv` (and any open CSVs in `extracted/`) in Excel or other spreadsheet apps before running the scripts so Windows does not block file writes with a `PermissionError`.
* Only pages with fewer than 15 selectable text words in both `pdfplumber` and `PyMuPDF` trigger OCR.
