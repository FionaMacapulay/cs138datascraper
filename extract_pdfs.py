import re
from pathlib import Path
import fitz
import pandas as pd
import pdfplumber
from rapidocr_onnxruntime import RapidOCR

INPUT_FOLDER = Path("pdfs")
OUTPUT_DIR = Path("extracted")
SKIP_EXISTING = True
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

PRODUCT_RANK = {p: i for i, p in enumerate(PRODUCT_ORDER)}

PRODUCT_PATTERNS = [
    ("RON 100", re.compile(r"\bR[O0]N\s*100\b")),
    ("RON 97", re.compile(r"\bR[O0]N\s*97\b")),
    ("RON 95", re.compile(r"\bR[O0]N\s*9[56]\b")),
    ("RON 91", re.compile(r"\bR[O0]N\s*91\b")),
    ("DIESEL PLUS", re.compile(r"\bDIESEL\s*PLUS\b")),
    ("DIESEL", re.compile(r"\bDIESEL\b")),
    ("KEROSENE", re.compile(r"\bKEROSENE\b")),
]

CYRILLIC_MAP = str.maketrans("АВЕКМНОРСТХавекмнорстх", "ABEKMHOPCTXabekmhopctx")

PROVINCE_FIXES = {
    "ILOCOSNORTE": "ILOCOS NORTE",
    "ILOCOSSUR": "ILOCOS SUR",
    "LAUNION": "LA UNION",
    "NUEVAVIZCAYA": "NUEVA VIZCAYA",
    "NUEVAECIJA": "NUEVA ECIJA",
}

ocr_engine = None


def get_ocr_engine():
    global ocr_engine
    if ocr_engine is None:
        ocr_engine = RapidOCR()
    return ocr_engine


def clean_text(text):
    if not text:
        return ""
    return " ".join(text.translate(CYRILLIC_MAP).split()).strip()


def extract_week_label(pdf_path):
    stem = pdf_path.stem
    match = re.search(
        r"(\d{1,2}\s*-\s*\d{1,2}\s+[A-Za-z]+\s+\d{4}|[A-Za-z]+\s+\d{1,2}\s*-\s*\d{1,2},?\s+\d{4})",
        stem,
    )
    if match:
        return clean_text(match.group(1))
    return stem


def safe_filename(label):
    return re.sub(r'[\\/:*?"<>|]', "_", label).strip()


def normalize_region(text):
    upper = clean_text(text).upper()
    if "CORDILLERA" in upper or "(CAR)" in upper:
        return "Cordillera Administrative Region (CAR)"
    if "CENTRAL" in upper:
        return "Central Luzon (REGION III)"
    if "CAGAYAN" in upper:
        return "Cagayan Valley (REGION II)"
    if "ILOCOS" in upper or "LLOCOS" in upper or "LOCOS" in upper:
        return "Ilocos Region (REGION I)"
    return ""


def extract_region(lines):
    for line in lines:
        region = normalize_region(" ".join(w["text"] for w in line))
        if region:
            return region
    return ""


def group_words_into_lines(words, y_tol=4.5):
    if not words:
        return []
    sorted_words = sorted(words, key=lambda w: (w["top"], w["x0"]))
    lines = []
    current = [sorted_words[0]]
    current_y = sorted_words[0]["top"]

    for word in sorted_words[1:]:
        if abs(word["top"] - current_y) <= y_tol:
            current.append(word)
        else:
            lines.append(sorted(current, key=lambda w: w["x0"]))
            current = [word]
            current_y = word["top"]

    lines.append(sorted(current, key=lambda w: w["x0"]))
    return lines


def extract_fitz_words(fitz_page):
    raw_words = fitz_page.get_text("words")
    return [
        {
            "text": w[4].strip(),
            "x0": w[0],
            "top": w[1],
            "x1": w[2],
            "bottom": w[3],
        }
        for w in raw_words
        if w[4].strip()
    ]


def ocr_page_to_words(fitz_page, zoom=2.0):
    pix = fitz_page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
    result, _ = get_ocr_engine()(pix.tobytes("png"))
    words = []
    if not result:
        return words

    for box, text, _ in result:
        cleaned = text.strip()
        if not cleaned:
            continue
        xs = [pt[0] / zoom for pt in box]
        ys = [pt[1] / zoom for pt in box]
        words.append({
            "text": cleaned,
            "x0": min(xs),
            "x1": max(xs),
            "top": min(ys),
            "bottom": max(ys),
        })
    return words

def deskew_words(words):
    prov_word = next((w for w in words if "PROVINCE" in w["text"].upper()), None)
    if not prov_word:
        return words

    hy = prov_word["top"]
    header_band = [w for w in words if abs(w["top"] - hy) <= 30]

    left_anchors = [
        w for w in header_band
        if any(k in w["text"].upper() for k in ("PROVINCE", "PRODUCT"))
    ]
    right_anchors = [
        w for w in header_band
        if any(k in w["text"].upper() for k in ("INDEPENDENT", "RANGE", "OVERALL"))
        and w["x0"] > 450
    ]

    if not left_anchors or not right_anchors:
        return words

    x_left = sum((w["x0"] + w["x1"]) / 2 for w in left_anchors) / len(left_anchors)
    y_left = sum((w["top"] + w["bottom"]) / 2 for w in left_anchors) / len(left_anchors)
    x_right = sum((w["x0"] + w["x1"]) / 2 for w in right_anchors) / len(right_anchors)
    y_right = sum((w["top"] + w["bottom"]) / 2 for w in right_anchors) / len(right_anchors)

    if x_right - x_left < 200:
        return words

    slope = (y_right - y_left) / (x_right - x_left)
    if abs(slope) > 0.05:
        return words

    deskewed = []
    for w in words:
        dy = slope * (w["x0"] - x_left)
        deskewed.append({
            **w,
            "top": w["top"] - dy,
            "bottom": w["bottom"] - dy,
        })
    return deskewed

def find_left_column_bounds(words, fallback_bounds=None):
    prov_word = None
    for w in words:
        if "PROVINCE" in w["text"].upper():
            prov_word = w
            break

    header_bottom = 0
    prov_max = None

    if prov_word:
        hy = prov_word["top"]
        header_band = [w for w in words if abs(w["top"] - hy) <= 22]
        city_words = [
            w for w in header_band
            if "CITY" in w["text"].upper() or "MUNICIPAL" in w["text"].upper()
        ]
        prod_words = [w for w in header_band if "PRODUCT" in w["text"].upper()]
        header_bottom = max(w["bottom"] for w in [prov_word] + city_words + prod_words)
        if city_words:
            prov_max = (prov_word["x1"] + min(w["x0"] for w in city_words)) / 2

    body_prod_x0 = [
        w["x0"] for w in words
        if w["top"] > header_bottom
        and re.match(r"^(RON|DIESEL|KEROSENE)\b", w["text"].upper())
    ]

    if body_prod_x0:
        prod_x0 = sorted(body_prod_x0)[len(body_prod_x0) // 2]
        if prov_max is None:
            prov_max = fallback_bounds["prov_max"] if fallback_bounds else prod_x0 * 0.45
        return {
            "prov_max": prov_max,
            "city_max": prod_x0 - 4,
            "prod_max": prod_x0 + 75,
            "header_bottom": header_bottom,
        }

    return fallback_bounds


def match_product(line, city_max, prod_max):
    prod_words = [
        w["text"] for w in line
        if city_max <= (w["x0"] + w["x1"]) / 2 <= prod_max
    ]
    text = " ".join(prod_words).upper()
    for name, pattern in PRODUCT_PATTERNS:
        if pattern.search(text):
            return name
    return None


def extract_common_price(line):
    if not line:
        return "-"
    rightmost = line[-1]["text"].strip()
    if "#" in rightmost or "N/A" in rightmost.upper():
        return "-"
    matches = re.findall(r"\d+\.\d{2}", rightmost)
    if matches:
        return float(matches[-1])
    match = re.search(r"\d+\.\d+", rightmost)
    return float(match.group()) if match else "-"


def join_place(words, is_province=False):
    if not words:
        return ""
    ordered = sorted(words, key=lambda w: (round(w["top"] / 5), w["x0"]))
    s = clean_text(" ".join(w["text"] for w in ordered)).upper()
    s = re.sub(r"([A-Z])CITY\b", r"\1 CITY", s)
    s = re.sub(r"\bCITYOF", "CITY OF ", s)
    s = re.sub(r"\bSCIENCECITY", "SCIENCE CITY", s)
    s = re.sub(r"\bSAN(FERNANDO|JOSE|CARLOS|RAFAEL)\b", r"SAN \1", s)
    s = re.sub(r"\s+", " ", s).strip()
    if is_province:
        compact = s.replace(" ", "")
        if compact in PROVINCE_FIXES:
            return PROVINCE_FIXES[compact]
    return s


def sort_df(df):
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


def parse_pdf(pdf_path, week_col):
    records = []
    fitz_doc = fitz.open(pdf_path)

    with pdfplumber.open(pdf_path) as pdf:
        last_region = ""
        last_province = ""
        last_bounds = None

        for idx, page in enumerate(pdf.pages):
            source = "pdfplumber"
            words = page.extract_words(
                x_tolerance=1.5,
                y_tolerance=2,
                keep_blank_chars=False,
                use_text_flow=False,
            )

            if len(words) < 15:
                fitz_words = extract_fitz_words(fitz_doc[idx])
                if len(fitz_words) >= 15:
                    words = fitz_words
                    source = "fitz"
                else:
                    words = ocr_page_to_words(fitz_doc[idx])
                    source = "ocr"

            if not words:
                print(f"  p{idx + 1} [{source}]: 0 words")
                continue

            words = deskew_words(words)
            y_tol = 4.5 if source == "ocr" else 2.5
            lines = group_words_into_lines(words, y_tol=y_tol)

            region = extract_region(lines) or last_region
            if region:
                last_region = region

            bounds = find_left_column_bounds(words, fallback_bounds=last_bounds)
            if not bounds:
                print(f"  p{idx + 1} [{source}]: no bounds")
                continue
            last_bounds = bounds

            prov_max = bounds["prov_max"]
            city_max = bounds["city_max"]
            prod_max = bounds["prod_max"]
            header_bottom = bounds["header_bottom"]

            product_rows = []
            for line in lines:
                y_top = min(w["top"] for w in line)
                if y_top <= header_bottom + 1:
                    continue
                prod = match_product(line, city_max, prod_max)
                if prod:
                    product_rows.append({
                        "top": y_top,
                        "bottom": max(w["bottom"] for w in line),
                        "product": prod,
                        "price": extract_common_price(line),
                    })

            blocks = []
            current_block = []
            for row in product_rows:
                if current_block and PRODUCT_RANK[row["product"]] <= PRODUCT_RANK[current_block[-1]["product"]]:
                    blocks.append(current_block)
                    current_block = [row]
                else:
                    current_block.append(row)
            if current_block:
                blocks.append(current_block)

            body_words = [w for w in words if w["top"] > header_bottom + 1]

            raw_block_provs = []
            for block in blocks:
                y_start = block[0]["top"] - 6
                y_end = block[-1]["bottom"] + 6
                p_words = [
                    w for w in body_words
                    if y_start <= w["top"] <= y_end and (w["x0"] + w["x1"]) / 2 < prov_max
                ]
                raw_block_provs.append(join_place(p_words, is_province=True))

            unique_page_provs = [p for p in dict.fromkeys(raw_block_provs) if p]

            for block, raw_prov in zip(blocks, raw_block_provs):
                y_start = block[0]["top"] - 6
                y_end = block[-1]["bottom"] + 6
                c_words = [
                    w for w in body_words
                    if y_start <= w["top"] <= y_end
                    and prov_max <= (w["x0"] + w["x1"]) / 2 < city_max
                ]
                city_name = join_place(c_words, is_province=False)

                if len(unique_page_provs) == 1:
                    prov_name = unique_page_provs[0]
                    last_province = prov_name
                elif raw_prov:
                    prov_name = raw_prov
                    last_province = prov_name
                else:
                    prov_name = last_province

                for row in block:
                    records.append({
                        "North Luzon": region,
                        "Province": prov_name,
                        "City": city_name,
                        "Product": row["product"],
                        week_col: row["price"],
                    })

            print(f"  p{idx + 1} [{source}]: {len(blocks)} cities, {len(product_rows)} rows")

    fitz_doc.close()
    df = pd.DataFrame(records, columns=KEY_COLS + [week_col])
    df = df.drop_duplicates(subset=KEY_COLS, keep="first")
    return sort_df(df)


OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
pdf_files = sorted(INPUT_FOLDER.glob("*.pdf"))

for pdf_path in pdf_files:
    week_col = extract_week_label(pdf_path)
    out_csv = OUTPUT_DIR / f"{safe_filename(week_col)}.csv"

    if SKIP_EXISTING and out_csv.exists():
        print(f"Skipped (already extracted): {out_csv.name}")
        continue

    print(f"Extracting {pdf_path.name} -> {out_csv.name}")
    week_df = parse_pdf(pdf_path, week_col)

    if week_df.empty:
        print(f"  No rows extracted from {pdf_path.name}")
        continue

    week_df.to_csv(out_csv, index=False)
    print(f"  Saved {len(week_df)} rows to {out_csv}")