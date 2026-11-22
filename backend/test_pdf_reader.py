import io

import pandas as pd
import pymupdf

from modules.pdf_reader import parse_soil_investigation_pdf, standardize_borehole_table


def _text_pdf(text: str) -> bytes:
    document = pymupdf.open()
    page = document.new_page()
    page.insert_text((72, 72), text)
    return document.tobytes()


def _grid_table_pdf() -> bytes:
    document = pymupdf.open()
    page = document.new_page(width=420, height=240)
    x_positions = [30, 150, 260, 330, 400]
    y_positions = [30, 70, 110, 150]
    shape = page.new_shape()
    for x_position in x_positions:
        shape.draw_line((x_position, y_positions[0]), (x_position, y_positions[-1]))
    for y_position in y_positions:
        shape.draw_line((x_positions[0], y_position), (x_positions[-1], y_position))
    shape.finish(color=(0, 0, 0), width=1)
    shape.commit()

    rows = [
        ["Kedalaman (m)", "Jenis Tanah", "N-SPT", "qc (MPa)"],
        ["0 - 2", "Lempung", "5", "0.25"],
        ["2 - 4", "Pasir", "12", "1.40"],
    ]
    for row_index, row in enumerate(rows):
        y_position = 55 + row_index * 40
        for column_index, value in enumerate(row):
            page.insert_text((x_positions[column_index] + 4, y_position), value, fontsize=9)
    return document.tobytes()


def test_standardize_alternate_headers_and_keep_missing_values_empty():
    raw_table = pd.DataFrame(
        {
            "Kedalaman (m)": ["0 - 2", "2 - 4"],
            "Klasifikasi Tanah": ["Lempung", "Pasir"],
            "N-SPT": [5, 12],
            "qc (MPa)": [None, 1.4],
            "\u03b3 (kN/m3)": [18.0, None],
            "c (kPa)": [20.0, None],
            "\u03c6 (deg)": [10.0, None],
            "Kadar Air (%)": [28.0, None],
        }
    )

    standardized = standardize_borehole_table(raw_table)

    assert standardized[["depth_from", "depth_to"]].values.tolist() == [[0.0, 2.0], [2.0, 4.0]]
    assert standardized["n_spt"].tolist() == [5.0, 12.0]
    assert pd.isna(standardized.loc[0, "qc"])
    assert pd.isna(standardized.loc[1, "gamma"])
    assert standardized.loc[0, "water_content_pct"] == 28.0


def test_parse_text_pdf_extracts_metadata_spt_qc_and_laboratory_data():
    pdf_bytes = _text_pdf(
        "Nama Proyek: Proyek Uji\n"
        "Lokasi: Bandung\n"
        "Titik Bor: BH-02\n"
        "MAT: 1.8 m\n"
        "0 - 2 m Lempung N-SPT=5 qc=0.25 MPa kadar air=28% LL=40 PL=22"
    )

    soil_data, metadata = parse_soil_investigation_pdf(io.BytesIO(pdf_bytes))
    diagnostics = metadata["diagnostics"]

    assert len(soil_data) == 1
    assert soil_data.loc[0, "depth_from"] == 0.0
    assert soil_data.loc[0, "depth_to"] == 2.0
    assert soil_data.loc[0, "n_spt"] == 5.0
    assert soil_data.loc[0, "qc"] == 0.25
    assert soil_data.loc[0, "water_content_pct"] == 28.0
    assert soil_data.loc[0, "liquid_limit_pct"] == 40.0
    assert soil_data.loc[0, "plastic_limit_pct"] == 22.0
    assert metadata["project_name"] == "Proyek Uji"
    assert metadata["location"] == "Bandung"
    assert metadata["borehole_id"] == "BH-02"
    assert metadata["ground_water_level"] == 1.8
    assert diagnostics["text_pages"] == [1]
    assert diagnostics["ocr_required_pages"] == []
    assert diagnostics["ocr_run"] is False


def test_parse_pdf_table_with_header_and_qc_values():
    soil_data, metadata = parse_soil_investigation_pdf(io.BytesIO(_grid_table_pdf()))
    diagnostics = metadata["diagnostics"]

    assert len(soil_data) == 2
    assert soil_data[["depth_from", "depth_to"]].values.tolist() == [[0.0, 2.0], [2.0, 4.0]]
    assert soil_data["qc"].tolist() == [0.25, 1.4]
    assert diagnostics["tables_detected"] == 1
    assert diagnostics["table_pages"] == [1]


def test_scanned_or_invalid_pdf_does_not_substitute_sample_data():
    document = pymupdf.open()
    document.new_page()
    soil_data, metadata = parse_soil_investigation_pdf(io.BytesIO(document.tobytes()))

    assert soil_data.empty
    assert metadata["borehole_id"] is None
    assert metadata["ground_water_level"] is None
    assert metadata["diagnostics"]["ocr_required_pages"] == [1]
    assert metadata["diagnostics"]["ocr_run"] is False
    assert "OCR belum dijalankan" in metadata["diagnostics"]["ocr_message"]

    invalid_data, invalid_metadata = parse_soil_investigation_pdf(b"not a PDF")
    assert invalid_data.empty
    assert invalid_metadata["diagnostics"]["tables_detected"] == 0