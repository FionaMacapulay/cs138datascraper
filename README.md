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

3. **Set your output file name**
   - Open `merge_csvs.py` and edit **line 7** (`OUTPUT_CSV = Path("doe_prices.csv")`) to match your assigned area (for example, `Path("doe_south_luzon_prices.csv")`, `Path("doe_visayas_prices.csv")`, or `Path("doe_mindanao_prices.csv")`).

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

8. **Clean using AI**
   - Some pages in the PDFs are not read cleanly by OCR.
   - Have AI clean up the merged sheet by fixing remaining OCR errors and merging rows/columns with similar patterns (for example, `NUEVA OCIJA` and `NUEVA ECIJA`).
