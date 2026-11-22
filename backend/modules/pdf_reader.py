"""
pdf_reader.py
Module for parsing soil investigation reports and borehole logs from PDF or tabular data.
Part of the GeoFoundation geotechnical analysis suite.
"""

import io
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import pandas as pd


SOIL_DATA_COLUMNS = [
    "depth_from",
    "depth_to",
    "soil_type",
    "description",
    "n_spt",
    "qc",
    "qc_unit",
    "gamma",
    "cohesion",
    "friction_angle",
    "water_content_pct",
    "liquid_limit_pct",
    "plastic_limit_pct",
    "specific_gravity",
    "void_ratio",
    "unconfined_compressive_strength_kpa",
]

NUMERIC_SOIL_COLUMNS = [
    column for column in SOIL_DATA_COLUMNS
    if column not in {"soil_type", "description", "qc_unit"}
]


def get_empty_soil_data() -> pd.DataFrame:
    """Returns an empty editable soil table without inserting example values."""
    return pd.DataFrame(columns=SOIL_DATA_COLUMNS)


def get_sample_soil_data() -> pd.DataFrame:
    """
    Returns a realistic standard geotechnical borehole log dataset (BH-01).
    Used as default sample data for demonstration, tests, and fallback.
    """
    data = [
        {
            "depth_from": 0.0,
            "depth_to": 2.0,
            "soil_type": "Lempung",
            "description": "Lempung lanauan sangat lunak, plastisitas tinggi, cokelat gelap",
            "n_spt": 3,
            "gamma": 15.5,
            "cohesion": 18.0,
            "friction_angle": 0.0,
        },
        {
            "depth_from": 2.0,
            "depth_to": 6.0,
            "soil_type": "Lempung Lanauan",
            "description": "Lempung lanauan dengan konsistensi sedang, abu-abu kekuningan",
            "n_spt": 8,
            "gamma": 16.8,
            "cohesion": 35.0,
            "friction_angle": 4.0,
        },
        {
            "depth_from": 6.0,
            "depth_to": 11.0,
            "soil_type": "Pasir",
            "description": "Pasir halus hingga sedang dengan kepadatan sedang, keabu-abuan",
            "n_spt": 18,
            "gamma": 18.2,
            "cohesion": 0.0,
            "friction_angle": 32.0,
        },
        {
            "depth_from": 11.0,
            "depth_to": 16.0,
            "soil_type": "Lempung Kaku",
            "description": "Lempung kaku hingga sangat kaku, cokelat kemerahan",
            "n_spt": 24,
            "gamma": 18.5,
            "cohesion": 75.0,
            "friction_angle": 8.0,
        },
        {
            "depth_from": 16.0,
            "depth_to": 22.0,
            "soil_type": "Pasir Padat",
            "description": "Pasir berlanau padat hingga sangat padat dengan kerikil, kekuningan",
            "n_spt": 42,
            "gamma": 19.5,
            "cohesion": 0.0,
            "friction_angle": 38.0,
        },
        {
            "depth_from": 22.0,
            "depth_to": 26.0,
            "soil_type": "Lempung Keras / Batu Lanau",
            "description": "Lempung lanauan keras bersemen atau batu lanau lapuk",
            "n_spt": 50,
            "gamma": 20.0,
            "cohesion": 120.0,
            "friction_angle": 15.0,
        },
    ]
    df = pd.DataFrame(data)
    return df


def _read_pdf_bytes(file_stream: Union[io.BytesIO, bytes, str]) -> bytes:
    if isinstance(file_stream, bytes):
        return file_stream
    if isinstance(file_stream, io.BytesIO):
        return file_stream.getvalue()
    if isinstance(file_stream, str):
        return Path(file_stream).read_bytes()
    raise TypeError("PDF harus berupa bytes, BytesIO, atau path berkas.")


def _table_header_index(rows: List[List[str]]) -> Optional[int]:
    keywords = (
        "depth", "kedalaman", "spt", "qc", "sondir", "soil", "tanah", "jenis",
        "description", "deskripsi", "lithology", "litologi", "gamma", "kohesi",
        "cohesion", "friction", "geser", "water content", "kadar air", "liquid limit",
        "batas cair", "plastic limit", "batas plastis", "parameter",
    )
    candidates = rows[: min(6, len(rows))]
    scores = [
        sum(any(keyword in cell.lower() for keyword in keywords) for cell in row)
        for row in candidates
    ]
    best_index = max(range(len(scores)), key=scores.__getitem__) if scores else 0
    return best_index if scores and scores[best_index] else None


def _extract_pdf_tables(pdf_bytes: bytes) -> Tuple[List[pd.DataFrame], List[int], Optional[str]]:
    import pdfplumber

    tables: List[pd.DataFrame] = []
    table_pages: List[int] = []
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page_number, page in enumerate(pdf.pages, start=1):
                for table in page.extract_tables() or []:
                    rows = [
                        [str(cell).strip() if cell is not None else "" for cell in row]
                        for row in table
                        if row and any(cell is not None and str(cell).strip() for cell in row)
                    ]
                    if not rows:
                        continue

                    column_count = max(len(row) for row in rows)
                    rows = [row + [""] * (column_count - len(row)) for row in rows]
                    header_index = _table_header_index(rows)
                    if header_index is None:
                        columns = [f"kolom_{index + 1}" for index in range(column_count)]
                        data_rows = rows
                    else:
                        columns = [cell or f"kolom_{index + 1}" for index, cell in enumerate(rows[header_index])]
                        data_rows = rows[header_index + 1:]
                    if not data_rows:
                        continue

                    frame = pd.DataFrame(data_rows, columns=columns).replace(r"^\s*$", pd.NA, regex=True)
                    frame = frame.dropna(how="all").reset_index(drop=True)
                    if not frame.empty:
                        tables.append(frame)
                        table_pages.append(page_number)
    except Exception as error:
        return tables, table_pages, str(error)
    return tables, table_pages, None


def inspect_pdf_document(file_stream: Union[io.BytesIO, bytes, str]) -> Tuple[str, List[pd.DataFrame], Dict[str, object]]:
    """Reads text with PyMuPDF and tables with pdfplumber, without running OCR."""
    pdf_bytes = _read_pdf_bytes(file_stream)
    diagnostics: Dict[str, object] = {
        "page_count": 0,
        "text_pages": [],
        "ocr_required_pages": [],
        "text_character_count": 0,
        "tables_detected": 0,
        "table_pages": [],
        "fitz_error": None,
        "pdfplumber_error": None,
        "ocr_run": False,
    }
    text_by_page: List[str] = []
    try:
        import pymupdf as fitz
        with fitz.open(stream=pdf_bytes, filetype="pdf") as pdf:
            diagnostics["page_count"] = len(pdf)
            for page_number, page in enumerate(pdf, start=1):
                page_text = page.get_text("text").strip()
                text_by_page.append(page_text)
                if page_text:
                    diagnostics["text_pages"].append(page_number)
                else:
                    diagnostics["ocr_required_pages"].append(page_number)
    except Exception as error:
        diagnostics["fitz_error"] = str(error)

    raw_text = "\n".join(text for text in text_by_page if text)
    if not raw_text.strip():
        try:
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
            diagnostics["page_count"] = diagnostics["page_count"] or len(reader.pages)
            text_by_page = [(page.extract_text() or "").strip() for page in reader.pages]
            raw_text = "\n".join(text for text in text_by_page if text)
            diagnostics["text_pages"] = [index for index, text in enumerate(text_by_page, start=1) if text]
            diagnostics["ocr_required_pages"] = [index for index, text in enumerate(text_by_page, start=1) if not text]
        except Exception as error:
            if not diagnostics["fitz_error"]:
                diagnostics["fitz_error"] = str(error)

    diagnostics["text_character_count"] = len(raw_text.strip())
    tables, table_pages, table_error = _extract_pdf_tables(pdf_bytes)
    diagnostics["tables_detected"] = len(tables)
    diagnostics["table_pages"] = table_pages
    diagnostics["pdfplumber_error"] = table_error
    return raw_text, tables, diagnostics


def parse_pdf_tables(file_stream: Union[io.BytesIO, bytes, str]) -> List[pd.DataFrame]:
    """Extracts tables from all pages while tolerating repeated or offset headers."""
    _, tables, _ = inspect_pdf_document(file_stream)
    return tables


def extract_text_from_pdf(file_stream: Union[io.BytesIO, bytes, str]) -> str:
    """Extracts selectable text from a PDF; scanned pages require separate OCR."""
    text, _, _ = inspect_pdf_document(file_stream)
    return text


def parse_soil_investigation_pdf(
    file_stream: Union[io.BytesIO, bytes, str]
) -> Tuple[pd.DataFrame, Dict[str, object]]:
    """Extracts actual soil data and PDF diagnostics; never substitutes sample data."""
    raw_text, tables, diagnostics = inspect_pdf_document(file_stream)
    metadata: Dict[str, object] = {
        "borehole_id": None,
        "project_name": None,
        "location": None,
        "ground_water_level": None,
        "diagnostics": diagnostics,
    }

    patterns = {
        "borehole_id": r"(?:Borehole|Boring|Titik\s+(?:Bor|Sondir)|Sondir|CPT)\s*(?:No\.?|ID|#)?\s*[:=\-]?\s*([A-Za-z0-9._/-]+)",
        "project_name": r"(?:Project|Proyek|Nama\s+Proyek)\s*[:=]\s*([^\r\n]{2,100})",
        "location": r"(?:Location|Lokasi|Site)\s*[:=]\s*([^\r\n]{2,100})",
    }
    for key, pattern in patterns.items():
        match = re.search(pattern, raw_text, re.IGNORECASE)
        if match:
            metadata[key] = match.group(1).strip(" .,:;-\t")

    gwl_match = re.search(
        r"(?:Ground\s*Water\s*Level|GWL|MAT|Muka\s*Air\s*Tanah|Water\s*Table)\s*[:=]?\s*(-?\d+(?:[.,]\d+)?)\s*m?\b",
        raw_text,
        re.IGNORECASE,
    )
    if gwl_match:
        metadata["ground_water_level"] = _to_number(gwl_match.group(1))

    extracted_frames = []
    for table in tables:
        standardized = standardize_borehole_table(table)
        if not standardized.empty:
            extracted_frames.append(standardized)

    if extracted_frames:
        soil_data = pd.concat(extracted_frames, ignore_index=True)
        soil_data = soil_data.drop_duplicates().reset_index(drop=True)
        diagnostics["data_source"] = "tabel"
    else:
        soil_data = parse_borehole_text_lines(raw_text)
        diagnostics["data_source"] = "teks" if not soil_data.empty else None

    extracted_fields = [
        column for column in SOIL_DATA_COLUMNS
        if column in soil_data and soil_data[column].notna().any()
        and (column not in {"soil_type", "description", "qc_unit"} or soil_data[column].astype(str).str.strip().ne("").any())
    ]
    diagnostics["extracted_fields"] = extracted_fields
    required_metadata = ("project_name", "location", "borehole_id", "ground_water_level")
    diagnostics["missing_metadata"] = [key for key in required_metadata if metadata[key] is None]
    diagnostics["ocr_message"] = (
        "OCR belum dijalankan. Halaman berikut tidak memiliki teks yang cukup dan memerlukan OCR: "
        + ", ".join(map(str, diagnostics["ocr_required_pages"]))
        if diagnostics["ocr_required_pages"] else "Tidak ada halaman yang terindikasi memerlukan OCR."
    )
    diagnostics["message"] = (
        "Data tanah tidak ditemukan pada teks atau tabel PDF."
        if soil_data.empty else "Data yang berhasil diekstrak siap diperiksa."
    )
    return soil_data, metadata


def _to_number(value: object) -> float:
    if value is None or pd.isna(value):
        return float("nan")
    match = re.search(r"[-+]?\d+(?:[.,]\d+)?", str(value).replace("\u00a0", " "))
    return float(match.group(0).replace(",", ".")) if match else float("nan")


def _depth_range(value: object) -> Optional[Tuple[float, float]]:
    if value is None or pd.isna(value):
        return None
    match = re.search(
        r"(-?\d+(?:[.,]\d+)?)\s*(?:-|\bto\b|sampai|s\.d\.?)\s*(-?\d+(?:[.,]\d+)?)",
        str(value),
        re.IGNORECASE,
    )
    if not match:
        return None
    return tuple(float(number.replace(",", ".")) for number in match.groups())


def _column_kind(column_name: object) -> Optional[str]:
    raw_name = str(column_name).lower()
    name = re.sub(r"[^a-z0-9]+", " ", str(column_name).lower()).strip()
    if any(term in name for term in ("depth range", "depth interval", "kedalaman lapisan", "rentang kedalaman", "interval kedalaman")) or name == "interval":
        return "depth_range"
    if "depth" in name or "kedalaman" in name or name in {"z", "elevasi"}:
        if any(term in name for term in ("from", "awal", "dari", "top", "atas")):
            return "depth_from"
        if any(term in name for term in ("to", "akhir", "sampai", "bottom", "bawah")):
            return "depth_to"
        return "depth_to"
    if "spt" in name or "n value" in name or "blow count" in name or name in {"n", "n 30", "n 60"}:
        return "n_spt"
    if re.search(r"\bqc\b", name) or "cone resistance" in name or "tahanan konus" in name or "perlawanan konus" in name:
        return "qc"
    if any(term in name for term in ("soil type", "soil classification", "jenis tanah", "klasifikasi tanah", "lithology", "litologi")):
        return "soil_type"
    if any(term in name for term in ("description", "deskripsi", "visual", "keterangan")):
        return "description"
    if "γ" in raw_name or any(term in name for term in ("gamma", "unit weight", "berat isi", "berat volume")):
        return "gamma"
    if any(term in name for term in ("cohesion", "kohesi")) or name in {"c", "cu"} or re.match(r"^c\s", name):
        return "cohesion"
    if "φ" in raw_name or any(term in name for term in ("friction angle", "sudut geser", "phi")):
        return "friction_angle"
    if any(term in name for term in ("water content", "moisture content", "kadar air")) or name in {"w", "wn"}:
        return "water_content_pct"
    if "liquid limit" in name or "batas cair" in name or name == "ll":
        return "liquid_limit_pct"
    if "plastic limit" in name or "batas plastis" in name or name == "pl":
        return "plastic_limit_pct"
    if "specific gravity" in name or "berat jenis" in name or name in {"gs", "g s"}:
        return "specific_gravity"
    if "void ratio" in name or "angka pori" in name or name == "e":
        return "void_ratio"
    if "unconfined" in name or "kuat tekan bebas" in name or name in {"qu", "q u"}:
        return "unconfined_compressive_strength_kpa"
    return None


def standardize_borehole_table(df: pd.DataFrame) -> pd.DataFrame:
    """Maps varied investigation-log headers without inventing missing measurements."""
    if df.empty:
        return get_empty_soil_data()

    normalized = pd.DataFrame(index=df.index)
    qc_unit = ""
    for column_index, column_name in enumerate(df.columns):
        kind = _column_kind(column_name)
        if kind is None:
            continue
        values = df.iloc[:, column_index]
        if kind in normalized:
            normalized[kind] = normalized[kind].combine_first(values)
        else:
            normalized[kind] = values
        if kind == "qc":
            unit_match = re.search(r"\(([^)]+)\)", str(column_name))
            if unit_match:
                qc_unit = unit_match.group(1).strip()

    if "depth_to" not in normalized and "depth_range" not in normalized:
        return get_empty_soil_data()

    range_source = normalized.get("depth_range", normalized.get("depth_to"))
    ranges = range_source.map(_depth_range)
    has_range = ranges.map(lambda value: value is not None)
    range_from = ranges.map(lambda value: value[0] if value else float("nan"))
    range_to = ranges.map(lambda value: value[1] if value else float("nan"))
    if "depth_to" in normalized:
        depth_to = normalized["depth_to"].map(_to_number)
        normalized["depth_to"] = range_to.where(has_range, depth_to)
    else:
        normalized["depth_to"] = range_to
    previous_depth = normalized["depth_to"].shift(1).fillna(0.0)
    if "depth_from" in normalized:
        depth_from = normalized["depth_from"].map(_to_number)
        normalized["depth_from"] = range_from.where(has_range, depth_from)
        normalized["depth_from"] = normalized["depth_from"].fillna(previous_depth)
    else:
        normalized["depth_from"] = range_from.fillna(previous_depth)

    for column in SOIL_DATA_COLUMNS:
        if column not in normalized:
            normalized[column] = "" if column in {"soil_type", "description", "qc_unit"} else float("nan")

    if not normalized["qc_unit"].astype(str).str.strip().any():
        normalized["qc_unit"] = qc_unit
    for column in NUMERIC_SOIL_COLUMNS:
        normalized[column] = normalized[column].map(_to_number)
    for column in ("soil_type", "description", "qc_unit"):
        normalized[column] = normalized[column].fillna("").astype(str).str.strip()

    has_measurement = normalized[[
        "soil_type", "description", "n_spt", "qc", "gamma", "cohesion", "friction_angle",
        "water_content_pct", "liquid_limit_pct", "plastic_limit_pct", "specific_gravity",
        "void_ratio", "unconfined_compressive_strength_kpa",
    ]].apply(
        lambda column: column.astype(str).str.strip().ne("") if column.dtype == object else column.notna()
    ).any(axis=1)
    valid_depth = normalized["depth_to"].notna() & normalized["depth_to"].gt(0)
    result = normalized.loc[valid_depth & has_measurement, SOIL_DATA_COLUMNS]
    return result.reset_index(drop=True) if not result.empty else get_empty_soil_data()


def parse_borehole_text_lines(raw_text: str) -> pd.DataFrame:
    """Extracts labeled depth intervals and measurements without estimating missing values."""
    records = []
    range_pattern = re.compile(
        r"(?P<start>-?\d+(?:[.,]\d+)?)\s*(?:-|\bto\b|sampai|s\.d\.?)\s*"
        r"(?P<end>-?\d+(?:[.,]\d+)?)\s*(?:m|meter)?\s*(?P<rest>.*)",
        re.IGNORECASE,
    )
    point_pattern = re.compile(r"(?:depth|kedalaman|z)\s*[:=]?\s*(?P<depth>\d+(?:[.,]\d+)?)\s*m?\b(.*)", re.IGNORECASE)
    n_pattern = re.compile(r"\b(?:n\s*[- ]?\s*spt|spt\s*n?|n\s*[- ]?\s*value|n)\b\s*[:=]?\s*(\d{1,3}(?:[.,]\d+)?)", re.IGNORECASE)
    qc_pattern = re.compile(r"\b(?:qc|qt)\b\s*[:=]?\s*(-?\d+(?:[.,]\d+)?)\s*([a-zA-Z²³/%]+(?:/[a-zA-Z²³]+)?)?", re.IGNORECASE)
    parameter_patterns = {
        "gamma": r"(?:gamma|unit\s*weight|berat\s*isi)\s*[:=]?\s*(-?\d+(?:[.,]\d+)?)",
        "cohesion": r"(?:cohesion|kohesi|\bc\b)\s*[:=]?\s*(-?\d+(?:[.,]\d+)?)",
        "friction_angle": r"(?:friction\s*angle|sudut\s*geser|phi|φ)\s*[:=]?\s*(-?\d+(?:[.,]\d+)?)",
        "water_content_pct": r"(?:water\s*content|moisture\s*content|kadar\s*air|\bw\b)\s*[:=]?\s*(-?\d+(?:[.,]\d+)?)",
        "liquid_limit_pct": r"(?:liquid\s*limit|batas\s*cair|\bll\b)\s*[:=]?\s*(-?\d+(?:[.,]\d+)?)",
        "plastic_limit_pct": r"(?:plastic\s*limit|batas\s plastis|\bpl\b)\s*[:=]?\s*(-?\d+(?:[.,]\d+)?)",
        "specific_gravity": r"(?:specific\s*gravity|berat\s*jenis|\bgs\b)\s*[:=]?\s*(-?\d+(?:[.,]\d+)?)",
        "void_ratio": r"(?:void\s*ratio|angka\s*pori)\s*[:=]?\s*(-?\d+(?:[.,]\d+)?)",
        "unconfined_compressive_strength_kpa": r"(?:unconfined\s*compressive|kuat\s*tekan\s*bebas|\bqu\b)\s*[:=]?\s*(-?\d+(?:[.,]\d+)?)",
    }

    for line in raw_text.splitlines():
        range_match = range_pattern.search(line)
        if range_match:
            depth_from = _to_number(range_match.group("start"))
            depth_to = _to_number(range_match.group("end"))
            rest = range_match.group("rest")
        else:
            point_match = point_pattern.search(line)
            if not point_match:
                continue
            depth_to = _to_number(point_match.group("depth"))
            depth_from = records[-1]["depth_to"] if records else 0.0
            rest = point_match.group(2)

        n_match = n_pattern.search(rest)
        qc_match = qc_pattern.search(rest)
        if not n_match and not qc_match and not re.search(r"[A-Za-zÀ-ÿ]", rest):
            continue

        description = n_pattern.sub("", rest)
        description = qc_pattern.sub("", description).strip(" \t:;|,-")
        for parameter_pattern in parameter_patterns.values():
            description = re.sub(parameter_pattern, "", description, flags=re.IGNORECASE)
        description = re.sub(r"\s+", " ", description).strip(" \t:;|,-")
        record = {
            "depth_from": depth_from,
            "depth_to": depth_to,
            "soil_type": description,
            "description": description,
            "n_spt": _to_number(n_match.group(1)) if n_match else float("nan"),
            "qc": _to_number(qc_match.group(1)) if qc_match else float("nan"),
            "qc_unit": qc_match.group(2) if qc_match and qc_match.group(2) else "",
        }
        for column, pattern in parameter_patterns.items():
            match = re.search(pattern, rest, re.IGNORECASE)
            record[column] = _to_number(match.group(1)) if match else float("nan")
        records.append(record)

    if not records:
        return get_empty_soil_data()
    return standardize_borehole_table(pd.DataFrame(records))


def infer_soil_type(description: str) -> str:
    """Classifies soil description into primary geotechnical soil types."""
    desc = description.lower()
    if "gravel" in desc or "kerikil" in desc:
        return "Gravel"
    elif "sand" in desc or "pasir" in desc:
        return "Sand"
    elif "silt" in desc or "lanau" in desc:
        return "Silt"
    elif "clay" in desc or "lempung" in desc:
        return "Clay"
    elif "peat" in desc or "gambut" in desc:
        return "Peat"
    elif "rock" in desc or "batuan" in desc:
        return "Rock"
    return "Mixed Soil"


def estimate_soil_parameters(soil_type: str, n_spt: float) -> Tuple[float, float, float]:
    """
    Empirical geotechnical correlations:
    Estimates (Unit Weight gamma [kN/m3], Cohesion c [kPa], Friction Angle phi [deg])
    from N-SPT and basic soil classification.
    """
    st = soil_type.lower()
    if "clay" in st or "lempung" in st:
        # Undrained shear strength cu approx 6.25 * N-SPT (Terzaghi & Peck)
        c = round(max(10.0, float(n_spt) * 6.25), 1)
        phi = 0.0
        gamma = round(min(20.0, 15.0 + 0.1 * n_spt), 1)
    elif "sand" in st or "pasir" in st or "gravel" in st:
        # Peck, Hanson, and Thornburn (1974)
        c = 0.0
        phi = round(min(45.0, 27.0 + 0.3 * n_spt), 1)
        gamma = round(min(21.0, 16.5 + 0.1 * n_spt), 1)
    elif "silt" in st or "lanau" in st:
        c = round(max(5.0, float(n_spt) * 3.5), 1)
        phi = round(min(32.0, 20.0 + 0.25 * n_spt), 1)
        gamma = round(min(19.0, 16.0 + 0.08 * n_spt), 1)
    else:
        c = 15.0
        phi = 25.0
        gamma = 17.5

    return gamma, c, phi
