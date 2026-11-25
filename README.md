# DOE Price Scraper

Extracts weekly common fuel prices from DOE PDFs and merges them into one CSV.

## Libraries Included

- `pdfplumber` — reads text from text-based PDFs
- `pymupdf` (`fitz`) — text fallback and renders image-only pages for OCR
- `rapidocr-onnxruntime` — OCR for pages with no selectable text
- `pandas` — merges, sorts, and saves CSV files

## Step-by-Step Setup & Usage

1. **Clone the repository**
   ```bash
   git clone <YOUR_GITHUB_REPO_URL>
   cd <repo-folder-name>
   ```

2. **Install the required libraries**
   ```bash
   python -m pip install -r requirements.txt
   ```

3. **Modify the scripts for your assigned region**
   - **In `extract_pdfs.py`:**
     - **`REGION_ORDER`:** Update the region list to match your assigned area.
     - **`normalize_region()`:** Update the keyword checks and return labels so each region in your PDFs maps to its standard name.
     - **`PROVINCE_FIXES` & `join_place()`:** Optional—if you aren't sure how to adjust these for your region's spacing or OCR quirks, leave them as-is and let AI clean them up in Step 9.
   - **In `merge_csvs.py`:**
     - **Line 7 (`OUTPUT_CSV`):** Change `OUTPUT_CSV = Path("doe_north_luzon_prices.csv")` to your desired output file name (for example, `Path("doe_south_luzon_prices.csv")`).
     - **`REGION_ORDER`:** Update to match `extract_pdfs.py`.
     - **Place/OCR cleanup (`build_canonical_maps()`, `repair_place_columns()`, & `sort_master_df()`):** Optional—if you aren't sure how to adjust these for your region, leave them as-is and let AI clean up the remaining OCR/row mismatches in Step 9.

4. **Add your PDFs**
   - Create a `pdfs/` folder in the project root.
   - Download all the weekly DOE PDF files for your assigned region and place them inside `pdfs/`.
   - Downloading PDFs in batches is recommended since there are many of them.

5. **Extract each PDF into its own CSV**
   - In your terminal (root folder), run:
     ```bash
     python extract_pdfs.py
     ```
   - Per-week CSVs are saved in `extracted/`.
   - *Optional:* Set `SKIP_EXISTING = False` in `extract_pdfs.py` to re-extract files already in `extracted/`.

6. **Merge all extracted weeks into one CSV**
   - After extraction is done, run:
     ```bash
     python merge_csvs.py
     ```
   - Combines everything into your configured output CSV, adding a column per week and new rows for new provinces or cities.

7. **Close open CSVs before re-running**
   - Close your output CSV (and any CSVs in `extracted/`) in Excel before running either script to avoid a `PermissionError`.

8. **Keep files clean before pushing to Git**
   - Make sure `.gitignore` excludes `pdfs/`, `extracted/`, and your local CSV outputs so you only push code and config files.

9. **Clean using AI**
   - Some pages in the PDFs are not read cleanly by OCR.
   - Have AI clean up the merged sheet by fixing remaining OCR errors and merging rows/columns with similar patterns (for example, `NUEVA OCIJA` and `NUEVA ECIJA`).
