# DOE Price Scraper

Extracts weekly common fuel prices from DOE PDFs and merges them into one CSV.

## Libraries Included:

* `pdfplumber` — reads text from text-based PDFs
* `pymupdf` (`fitz`) — text fallback and renders image-only pages for OCR
* `rapidocr-onnxruntime` — OCR for pages with no selectable text
* `pandas` — merges, sorts, and saves CSV files

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

3. **Add your PDFs**
   * Create a `pdfs/` folder in the project root.
   * Download all the weekly DOE PDF files and place inside `pdfs/`.

4. **Extract each PDF into its own CSV**
   * On your terminal (root folder), run:
    ```bash
   python extract_pdfs.py
   ```
   * Per-week CSVs are saved in `extracted/`.
   * OPTIONAL: Set `SKIP_EXISTING = False` in `extract_pdfs.py` to re-extract files already in `extracted/`.

6. **Merge all extracted weeks into one CSV**
   * After the extraction is done, run this on your terminal:
   ```bash
   python merge_csvs.py
   ```
   * Combines everything into `doe_north_luzon_prices.csv`, adding a column per week and new rows for new provinces or cities.

8. **Close open CSVs before re-running**
   * Close `doe_north_luzon_prices.csv` (and any CSVs in `extracted/`) in Excel before running either script to avoid a `PermissionError`.
