"""
test_calculation.py
Unit tests for geotechnical foundation calculations in GeoFoundation.
Tests shallow foundation, deep foundation, bearing capacity factors, and pile groups.
"""

import pytest
import pandas as pd
from modules.foundation_calculation import (
    get_bearing_capacity_factors,
    calculate_shallow_foundation,
    calculate_single_pile_capacity,
    calculate_pile_capacity_depth_profile,
    calculate_pile_group,
)
from modules.pdf_reader import get_sample_soil_data


def test_bearing_capacity_factors_phi_zero():
    """Test bearing capacity factors for undrained clay (phi = 0)."""
    factors_meyerhof = get_bearing_capacity_factors(0.0, method="meyerhof")
    assert factors_meyerhof["Nc"] == 5.14
    assert factors_meyerhof["Nq"] == 1.0
    assert factors_meyerhof["Ngamma"] == 0.0

    factors_terzaghi = get_bearing_capacity_factors(0.0, method="terzaghi")
    assert factors_terzaghi["Nc"] == 5.70
    assert factors_terzaghi["Nq"] == 1.0
    assert factors_terzaghi["Ngamma"] == 0.0


def test_bearing_capacity_factors_phi_30():
    """Test bearing capacity factors for phi = 30 degrees."""
    factors = get_bearing_capacity_factors(30.0, method="meyerhof")
    assert factors["Nq"] > 18.0 and factors["Nq"] < 19.0
    assert factors["Nc"] > 30.0 and factors["Nc"] < 31.0
    assert factors["Ngamma"] > 15.0


def test_shallow_foundation_strip_footing():
    """Test shallow strip foundation calculation."""
    res = calculate_shallow_foundation(
        footing_type="strip",
        width_b=2.0,
        length_l=2.0,
        depth_df=1.5,
        cohesion_c=20.0,
        phi_deg=25.0,
        unit_weight_gamma=18.0,
        applied_load_p=250.0,
        safety_factor=3.0,
        method="meyerhof",
    )
    assert res["q_ult_kpa"] > 0
    assert res["q_all_kpa"] == round(res["q_ult_kpa"] / 3.0, 2)
    assert res["shape_factors"]["sc"] == 1.0
    assert res["shape_factors"]["sq"] == 1.0
    assert res["shape_factors"]["sgamma"] == 1.0


def test_shallow_foundation_groundwater_influence():
    """Test that high groundwater table reduces bearing capacity."""
    # Water table deep below footing
    res_dry = calculate_shallow_foundation(
        footing_type="square",
        width_b=2.0,
        length_l=2.0,
        depth_df=1.5,
        cohesion_c=10.0,
        phi_deg=30.0,
        unit_weight_gamma=18.0,
        gwl_depth=10.0,
        gamma_sat=20.0,
    )
    # Water table at surface (submerged)
    res_submerged = calculate_shallow_foundation(
        footing_type="square",
        width_b=2.0,
        length_l=2.0,
        depth_df=1.5,
        cohesion_c=10.0,
        phi_deg=30.0,
        unit_weight_gamma=18.0,
        gwl_depth=0.0,
        gamma_sat=20.0,
    )

    assert res_submerged["q_ult_kpa"] < res_dry["q_ult_kpa"]
    assert "Case 1" in res_submerged["gwl_case"]


def test_single_pile_capacity():
    """Test single pile capacity calculation from soil profile."""
    df_soil = get_sample_soil_data()
    res_meyerhof = calculate_single_pile_capacity(
        df_soil=df_soil,
        pile_type="driven",
        diameter=0.5,
        pile_length=15.0,
        method="meyerhof",
    )

    assert res_meyerhof["q_shaft_friction_kn"] > 0
    assert res_meyerhof["q_end_bearing_kn"] > 0
    assert res_meyerhof["q_ult_kn"] == pytest.approx(
        res_meyerhof["q_end_bearing_kn"] + res_meyerhof["q_shaft_friction_kn"], abs=0.05
    )
    assert res_meyerhof["q_all_dual_sf_kn"] < res_meyerhof["q_ult_kn"]

    # Decourt method test
    res_decourt = calculate_single_pile_capacity(
        df_soil=df_soil,
        pile_type="driven",
        diameter=0.5,
        pile_length=15.0,
        method="decourt",
    )
    assert res_decourt["q_ult_kn"] > 0


def test_pile_capacity_depth_profile():
    """Test pile capacity curve generation across depths."""
    df_soil = get_sample_soil_data()
    df_profile = calculate_pile_capacity_depth_profile(
        df_soil=df_soil,
        pile_type="driven",
        diameter=0.4,
        min_depth=4.0,
        max_depth=12.0,
        step=2.0,
    )
    assert not df_profile.empty
    assert len(df_profile) == 5
    # As depth increases, capacity should increase monotonically in this stratified soil
    assert df_profile["q_ult_kn"].iloc[-1] > df_profile["q_ult_kn"].iloc[0]


def test_pile_group_efficiency():
    """Test Converse-Labarre group efficiency calculation."""
    # Single pile
    res_single = calculate_pile_group(1, 1, spacing=1.5, diameter=0.5, single_q_ult=1000.0, single_q_all=400.0)
    assert res_single["efficiency"] == 1.0
    assert res_single["group_q_ult_kn"] == 1000.0

    # 3x3 group
    res_group = calculate_pile_group(3, 3, spacing=1.5, diameter=0.5, single_q_ult=1000.0, single_q_all=400.0)
    assert res_group["total_piles"] == 9
    assert 0.5 < res_group["efficiency"] < 1.0
    # Group capacity uses full floating-point Converse-Labarre eta before 3-decimal display rounding
    assert res_group["group_q_ult_kn"] == pytest.approx(res_group["efficiency"] * 9 * 1000.0, abs=1.5)
