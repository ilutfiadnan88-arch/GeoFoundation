"""
test_chat_copilot.py
Unit tests for the GeoCopilot geotechnical assistant module.
Verifies response generation, project data integration, and quick access topics.
"""

import pandas as pd
import pytest

from modules.chat_copilot import (
    QUICK_ACCESS_TOPICS,
    generate_geotechnical_response,
)
from modules.pdf_reader import get_sample_soil_data


def test_quick_access_topics_structure():
    """Verify all 4 quick access topics are defined with required attributes."""
    assert len(QUICK_ACCESS_TOPICS) == 4
    topic_ids = [t["id"] for t in QUICK_ACCESS_TOPICS]
    assert "stratigrafi" in topic_ids
    assert "spt_cpt" in topic_ids
    assert "kapasitas_fondasi" in topic_ids
    assert "standar_geoteknik" in topic_ids

    for topic in QUICK_ACCESS_TOPICS:
        assert topic["title"]
        assert topic["desc"]
        assert topic["prompt"]


def test_stratigraphy_analysis_response():
    """Test response to stratigraphy query with active soil data."""
    soil_df = get_sample_soil_data()
    metadata = {
        "borehole_id": "BH-01",
        "project_name": "Gedung Uji",
        "data_kind": "demonstrasi",
        "gwl": 2.5,
    }

    response = generate_geotechnical_response("Analisis stratigrafi lapisan tanah", soil_df, metadata)
    assert "BH-01" in response
    assert any(w in response for w in ["Lempung", "Pasir", "Clay", "Sand"])
    assert "2.50 m" in response
    assert "Status Data:" in response


def test_spt_interpretation_response():
    """Test response to SPT and CPT interpretation query."""
    soil_df = get_sample_soil_data()
    metadata = {
        "borehole_id": "BH-02",
        "project_name": "Jembatan",
        "data_kind": "hasil ekstraksi PDF",
        "gwl": 1.8,
    }

    response = generate_geotechnical_response("Interpretasi data N-SPT dan konsistensi", soil_df, metadata)
    assert "Tahanan Penetrasi Standar (N-SPT)" in response
    assert "BH-02" in response
    assert "SNI 8460:2017" in response


def test_foundation_calculation_integration():
    """Test foundation query incorporating active calculation results."""
    soil_df = get_sample_soil_data()
    metadata = {
        "borehole_id": "BH-01",
        "project_name": "Pondasi Gedung",
        "data_kind": "demonstrasi",
        "gwl": 2.0,
        "shallow_res": {
            "footing_type": "Persegi",
            "dimensions": "2.00 m x 2.00 m",
            "q_ult_kpa": 450.0,
            "q_all_kpa": 150.0,
            "q_applied_kpa": 120.0,
            "actual_sf": 3.75,
            "required_sf": 3.0,
            "is_safe": True,
        },
        "pile_res": {
            "pile_type": "Tiang Pancang",
            "pile_diameter_m": 0.5,
            "pile_length_m": 14.0,
            "q_end_bearing_kn": 600.0,
            "q_shaft_friction_kn": 800.0,
            "q_ult_kn": 1400.0,
            "q_all_dual_sf_kn": 600.0,
        },
    }

    response = generate_geotechnical_response("Perhitungan kapasitas fondasi dangkal dan dalam", soil_df, metadata)
    assert "Meyerhof" in response
    assert "Terzaghi" in response
    assert "150.0 kPa" in response
    assert "1400.0 kN" in response


def test_standards_response():
    """Test response to standards and geotechnical references query."""
    soil_df = pd.DataFrame()
    metadata = {"borehole_id": "BH-01", "project_name": "Proyek", "data_kind": "manual"}

    response = generate_geotechnical_response("Standar dan acuan SNI", soil_df, metadata)
    assert "SNI 8460:2017" in response
    assert "Meyerhof" in response
    assert "Decourt" in response
