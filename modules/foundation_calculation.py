"""
foundation_calculation.py
Geotechnical engineering calculation module for shallow and deep foundations.
Includes Terzaghi, Meyerhof, and Luciano Decourt formulations, groundwater effects,
and pile group efficiency.
Part of the GeoFoundation geotechnical analysis suite.
"""

import math
from typing import Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd


# -----------------------------------------------------------------------------
# Bearing Capacity Factors (N_c, N_q, N_gamma)
# -----------------------------------------------------------------------------

def get_bearing_capacity_factors(phi_deg: float, method: str = "meyerhof") -> Dict[str, float]:
    """
    Computes bearing capacity factors (Nc, Nq, Ngamma) for a given friction angle (phi).
    Supports 'meyerhof', 'terzaghi', 'vesic', and 'hansen'.
    """
    phi_rad = math.radians(phi_deg)

    if phi_deg == 0.0:
        if method == "terzaghi":
            return {"Nc": 5.70, "Nq": 1.0, "Ngamma": 0.0}
        else:
            return {"Nc": 5.14, "Nq": 1.0, "Ngamma": 0.0}

    # Common Nq for Meyerhof, Hansen, Vesic
    nq = math.exp(math.pi * math.tan(phi_rad)) * (math.tan(math.radians(45.0 + phi_deg / 2.0)) ** 2)
    nc = (nq - 1.0) / math.tan(phi_rad)

    if method == "terzaghi":
        # Terzaghi formulation approximation (Kumbhojkar 1993)
        nq_t = (math.exp((1.5 * math.pi - phi_rad) * math.tan(phi_rad))) / (
            2.0 * (math.cos(math.radians(45.0 + phi_deg / 2.0)) ** 2)
        )
        nc_t = (nq_t - 1.0) / math.tan(phi_rad)
        # Kumbhojkar fit for Terzaghi Ngamma
        ngamma_t = 2.0 * (nq_t + 1.0) * math.tan(phi_rad) * 0.5  # practical formulation
        return {"Nc": round(nc_t, 3), "Nq": round(nq_t, 3), "Ngamma": round(ngamma_t, 3)}

    elif method == "vesic":
        ngamma = 2.0 * (nq + 1.0) * math.tan(phi_rad)
    elif method == "hansen":
        ngamma = 1.5 * (nq - 1.0) * math.tan(phi_rad)
    else:
        # Meyerhof (1963)
        ngamma = (nq - 1.0) * math.tan(math.radians(1.4 * phi_deg))

    return {
        "Nc": round(nc, 3),
        "Nq": round(nq, 3),
        "Ngamma": round(ngamma, 3),
    }


# -----------------------------------------------------------------------------
# Shallow Foundation (Pondasi Dangkal)
# -----------------------------------------------------------------------------

def calculate_shallow_foundation(
    footing_type: str,           # 'square', 'strip', 'circular', 'rectangular'
    width_b: float,              # m (Footing width B)
    length_l: float,             # m (Footing length L, B <= L)
    depth_df: float,             # m (Embedment depth Df)
    cohesion_c: float,           # kPa (c or cu)
    phi_deg: float,              # degrees (internal friction angle)
    unit_weight_gamma: float,    # kN/m3 (soil unit weight above water table)
    gwl_depth: Optional[float] = None, # m (depth of ground water level from surface)
    gamma_sat: float = 19.0,     # kN/m3 (saturated soil unit weight)
    gamma_water: float = 9.81,   # kN/m3 (water unit weight)
    applied_load_p: float = 0.0, # kN (Design column load P)
    safety_factor: float = 3.0,  # FS allowable
    method: str = "meyerhof"     # 'meyerhof' or 'terzaghi'
) -> Dict[str, Union[float, str, Dict[str, float]]]:
    """
    Computes ultimate and allowable bearing capacity of shallow footings,
    considering groundwater table conditions, shape, and depth factors.
    """
    footing_type = footing_type.lower()
    factors = get_bearing_capacity_factors(phi_deg, method=method)
    nc, nq, ngamma = factors["Nc"], factors["Nq"], factors["Ngamma"]

    # 1. Effective Surcharge (q') at foundation level (depth Df)
    gamma_sub = max(0.0, gamma_sat - gamma_water)

    if gwl_depth is None or gwl_depth >= depth_df + width_b:
        # Case 3: Water table deeper than Df + B
        q_surcharge = unit_weight_gamma * depth_df
        gamma_eff_b = unit_weight_gamma
        gwl_case = "Case 3: Water table well below influence depth (d_w >= Df + B)"
    elif gwl_depth <= depth_df:
        # Case 1: Water table at or above footing base
        h1 = max(0.0, gwl_depth)
        h2 = depth_df - h1
        q_surcharge = (unit_weight_gamma * h1) + (gamma_sub * h2)
        gamma_eff_b = gamma_sub
        gwl_case = "Case 1: Water table at or above footing base (d_w <= Df)"
    else:
        # Case 2: Water table within distance B below base (Df < d_w < Df + B)
        q_surcharge = unit_weight_gamma * depth_df
        d_sub = gwl_depth - depth_df
        gamma_eff_b = gamma_sub + (d_sub / width_b) * (unit_weight_gamma - gamma_sub)
        gwl_case = "Case 2: Water table within depth B below footing (Df < d_w < Df + B)"

    # 2. Shape and Depth Factors
    # Terzaghi factors
    if method == "terzaghi":
        if footing_type == "strip":
            sc, sq, sgamma = 1.0, 1.0, 1.0
        elif footing_type == "square":
            sc, sq, sgamma = 1.3, 1.0, 0.8
        elif footing_type == "circular":
            sc, sq, sgamma = 1.3, 1.0, 0.6
        else:  # rectangular
            sc = 1.0 + 0.2 * (width_b / length_l)
            sq = 1.0
            sgamma = 1.0 - 0.2 * (width_b / length_l)
        dc, dq, dgamma = 1.0, 1.0, 1.0  # Terzaghi does not incorporate depth factors directly
    else:
        # Meyerhof (1963) factors
        phi_rad = math.radians(phi_deg)
        kp = math.tan(math.radians(45.0 + phi_deg / 2.0)) ** 2

        # Shape factors
        if footing_type == "strip":
            sc, sq, sgamma = 1.0, 1.0, 1.0
        else:
            b_over_l = width_b / length_l if length_l > 0 else 1.0
            sc = 1.0 + 0.2 * kp * b_over_l
            if phi_deg > 10.0:
                sq = 1.0 + 0.1 * kp * b_over_l
                sgamma = sq
            else:
                sq = 1.0
                sgamma = 1.0

        # Depth factors
        df_over_b = depth_df / width_b if width_b > 0 else 0.0
        sqrt_kp = math.sqrt(kp)
        dc = 1.0 + 0.2 * sqrt_kp * df_over_b
        if phi_deg > 10.0:
            dq = 1.0 + 0.1 * sqrt_kp * df_over_b
            dgamma = dq
        else:
            dq = 1.0
            dgamma = 1.0

    # 3. Ultimate Bearing Capacity components
    term_c = cohesion_c * nc * sc * dc
    term_q = q_surcharge * nq * sq * dq
    term_gamma = 0.5 * gamma_eff_b * width_b * ngamma * sgamma * dgamma

    q_ult = term_c + term_q + term_gamma
    q_all = q_ult / safety_factor
    q_net_all = (q_ult - q_surcharge) / safety_factor

    # 4. Footing Area & Loading Check
    if footing_type == "circular":
        area = math.pi * ((width_b / 2.0) ** 2)
    elif footing_type == "strip":
        area = width_b * 1.0  # per meter run
    else:
        area = width_b * length_l

    concrete_unit_weight = 24.0  # kN/m3
    w_foundation = area * depth_df * concrete_unit_weight if area > 0 else 0.0
    total_vertical_load = applied_load_p + w_foundation
    
    q_applied = (total_vertical_load / area) if area > 0 else 0.0
    is_safe = bool(q_applied <= q_all) if applied_load_p > 0 else True
    actual_sf = round(q_ult / q_applied, 2) if q_applied > 0 else 999.0

    return {
        "method": method.capitalize(),
        "footing_type": footing_type.capitalize(),
        "dimensions": f"{width_b:.2f} m x {length_l:.2f} m (Df = {depth_df:.2f} m)",
        "area": round(area, 2),
        "gwl_case": gwl_case,
        "effective_surcharge_q": round(q_surcharge, 2),
        "effective_gamma": round(gamma_eff_b, 2),
        "factors": {"Nc": nc, "Nq": nq, "Ngamma": ngamma},
        "shape_factors": {"sc": round(sc, 3), "sq": round(sq, 3), "sgamma": round(sgamma, 3)},
        "depth_factors": {"dc": round(dc, 3), "dq": round(dq, 3), "dgamma": round(dgamma, 3)},
        "bearing_components": {
            "cohesion_term_qc": round(term_c, 2),
            "surcharge_term_qq": round(term_q, 2),
            "unit_weight_term_qgamma": round(term_gamma, 2),
        },
        "q_ult_kpa": round(q_ult, 2),
        "q_all_kpa": round(q_all, 2),
        "q_net_all_kpa": round(q_net_all, 2),
        "applied_load_p_kn": round(applied_load_p, 2),
        "foundation_self_weight_kn": round(w_foundation, 2),
        "q_applied_kpa": round(q_applied, 2),
        "actual_sf": actual_sf,
        "required_sf": safety_factor,
        "is_safe": is_safe,
    }


# -----------------------------------------------------------------------------
# Deep Foundation (Pondasi Tiang Pancang / Bored Pile)
# -----------------------------------------------------------------------------

def calculate_single_pile_capacity(
    df_soil: pd.DataFrame,
    pile_type: str = "driven",      # 'driven' or 'bored'
    diameter: float = 0.5,          # m (Pile diameter or equivalent width)
    pile_length: float = 15.0,      # m (Total embedded pile length)
    method: str = "meyerhof",       # 'meyerhof' or 'decourt'
    safety_factor_end: float = 3.0,
    safety_factor_shaft: float = 2.0,
    safety_factor_total: float = 2.5
) -> Dict[str, Union[float, str, List[Dict[str, float]]]]:
    """
    Calculates single pile axial compression capacity from N-SPT profile.
    Uses either Meyerhof (1976) or Luciano Decourt (1996) method.
    """
    pile_type = pile_type.lower()
    method = method.lower()
    perimeter = math.pi * diameter
    base_area = (math.pi / 4.0) * (diameter ** 2)

    shaft_layers = []
    q_shaft_total = 0.0

    # Layer-by-layer skin friction integration along embedded pile length
    for _, row in df_soil.iterrows():
        z_from = float(row["depth_from"])
        z_to = float(row["depth_to"])

        if z_from >= pile_length:
            continue

        # Effective slice embedded
        top_z = max(0.0, z_from)
        bot_z = min(pile_length, z_to)
        dz = bot_z - top_z
        if dz <= 0:
            continue

        nspt = float(row.get("n_spt", 10.0))
        stype = str(row.get("soil_type", "")).lower()
        is_cohesive = any(c in stype for c in ["clay", "lempung", "silt", "lanau"])

        # Unit skin friction (fs in kPa)
        if method == "decourt":
            # Decourt (1996): fs = alpha * (N_s / 3 + 1) in kPa
            # alpha = 10 for sand, 12 for clay
            alpha = 12.0 if is_cohesive else 10.0
            fs = alpha * ((nspt / 3.0) + 1.0)
            if pile_type == "bored":
                fs *= 0.8  # reduction for bored piles
        else:
            # Meyerhof (1976):
            if is_cohesive:
                # fs = alpha * cu approx 0.5 * 6.25 * N = 3.125 * N kPa
                fs = min(100.0, 3.125 * nspt)
            else:
                # Sand: fs = 2 * N (driven) or 1 * N (bored) kPa
                mult = 1.0 if pile_type == "bored" else 2.0
                fs = min(120.0, mult * nspt)

        layer_as = perimeter * dz
        layer_qs = fs * layer_as
        q_shaft_total += layer_qs

        shaft_layers.append({
            "depth_range": f"{top_z:.1f} - {bot_z:.1f} m",
            "soil_type": row.get("soil_type", "Soil"),
            "n_spt": nspt,
            "unit_friction_kpa": round(fs, 2),
            "layer_area_m2": round(layer_as, 2),
            "friction_kn": round(layer_qs, 2),
        })

    # End Bearing Capacity (Base resistance)
    # Get N-SPT around the tip (4D above to 1D below tip)
    tip_z = pile_length
    window_top = max(0.0, tip_z - 4 * diameter)
    window_bot = tip_z + 1 * diameter

    tip_spt_candidates = []
    tip_soil_type = "sand"
    for _, row in df_soil.iterrows():
        if row["depth_to"] >= window_top and row["depth_from"] <= window_bot:
            tip_spt_candidates.append(float(row.get("n_spt", 15.0)))
            tip_soil_type = str(row.get("soil_type", tip_soil_type)).lower()

    n_tip_avg = float(np.mean(tip_spt_candidates)) if tip_spt_candidates else 20.0
    is_tip_cohesive = any(c in tip_soil_type for c in ["clay", "lempung", "silt", "lanau"])

    if method == "decourt":
        # Decourt: qp = C * N_tip (C = 400 for sand, 250 for clay, 120 for silt)
        if "clay" in tip_soil_type or "lempung" in tip_soil_type:
            c_base = 250.0
        elif "silt" in tip_soil_type or "lanau" in tip_soil_type:
            c_base = 120.0
        else:
            c_base = 400.0
        
        qb = c_base * n_tip_avg
        if pile_type == "bored":
            qb *= 0.6  # Base softening for bored piles
    else:
        # Meyerhof (1976):
        # Driven sand: qb = 40 * N * (L/D) <= 400 * N (kPa)
        # Driven clay: qb = 9 * cu = 9 * (6.25 * N) = 56.25 * N (kPa)
        l_over_d = pile_length / diameter if diameter > 0 else 10.0
        if is_tip_cohesive:
            qb = min(4000.0, 56.25 * n_tip_avg)
        else:
            qb = min(400.0 * n_tip_avg, 40.0 * n_tip_avg * min(l_over_d, 10.0))

        if pile_type == "bored":
            qb *= 0.5  # Standard bored pile reduction

    q_base_total = qb * base_area
    q_ult = q_base_total + q_shaft_total

    # Allowable Capacities
    # Dual safety factor: SF_end=3.0, SF_shaft=2.0
    q_all_dual = (q_base_total / safety_factor_end) + (q_shaft_total / safety_factor_shaft)
    # Overall safety factor: SF=2.5
    q_all_overall = q_ult / safety_factor_total

    return {
        "method": method.capitalize(),
        "pile_type": pile_type.capitalize(),
        "pile_diameter_m": round(diameter, 2),
        "pile_length_m": round(pile_length, 2),
        "base_area_m2": round(base_area, 4),
        "perimeter_m": round(perimeter, 3),
        "n_tip_average": round(n_tip_avg, 1),
        "unit_end_bearing_kpa": round(qb, 2),
        "q_end_bearing_kn": round(q_base_total, 2),
        "q_shaft_friction_kn": round(q_shaft_total, 2),
        "q_ult_kn": round(q_ult, 2),
        "q_all_dual_sf_kn": round(q_all_dual, 2),
        "q_all_overall_sf_kn": round(q_all_overall, 2),
        "safety_factor_end": safety_factor_end,
        "safety_factor_shaft": safety_factor_shaft,
        "safety_factor_total": safety_factor_total,
        "layers": shaft_layers,
    }


def calculate_pile_capacity_depth_profile(
    df_soil: pd.DataFrame,
    pile_type: str = "driven",
    diameter: float = 0.5,
    min_depth: float = 3.0,
    max_depth: Optional[float] = None,
    step: float = 1.0,
    method: str = "meyerhof"
) -> pd.DataFrame:
    """
    Computes single pile capacity at multiple depths to generate
    capacity vs. depth design curves.
    """
    if max_depth is None:
        max_depth = float(df_soil["depth_to"].max()) if not df_soil.empty else 20.0

    depths = np.arange(min_depth, max_depth + 0.1, step)
    records = []

    for depth in depths:
        res = calculate_single_pile_capacity(
            df_soil,
            pile_type=pile_type,
            diameter=diameter,
            pile_length=float(depth),
            method=method,
        )
        records.append({
            "depth_m": round(depth, 1),
            "q_end_kn": res["q_end_bearing_kn"],
            "q_shaft_kn": res["q_shaft_friction_kn"],
            "q_ult_kn": res["q_ult_kn"],
            "q_all_kn": res["q_all_dual_sf_kn"],
        })

    return pd.DataFrame(records)


def calculate_pile_group(
    n_rows: int,
    n_cols: int,
    spacing: float,              # m (center to center pile spacing, typically 2.5D - 3.5D)
    diameter: float,            # m
    single_q_ult: float,        # kN
    single_q_all: float         # kN
) -> Dict[str, Union[float, int]]:
    """
    Computes pile group capacity and efficiency using the Converse-Labarre formula.
    """
    total_piles = n_rows * n_cols
    if total_piles <= 1:
        return {
            "total_piles": 1,
            "efficiency": 1.0,
            "group_q_ult_kn": single_q_ult,
            "group_q_all_kn": single_q_all,
            "spacing_ratio": spacing / diameter if diameter > 0 else 3.0,
        }

    # Converse-Labarre equation:
    # eta = 1 - [arctan(d/s) * ((n-1)*m + (m-1)*n) / (90 * m * n)]
    theta_deg = math.degrees(math.atan(diameter / spacing))
    m = n_rows
    n = n_cols
    eta = 1.0 - (theta_deg * (((n - 1) * m) + ((m - 1) * n))) / (90.0 * m * n)
    eta = max(0.4, min(1.0, eta))  # realistic bounds

    group_q_ult = eta * total_piles * single_q_ult
    group_q_all = eta * total_piles * single_q_all

    return {
        "n_rows": n_rows,
        "n_cols": n_cols,
        "total_piles": total_piles,
        "efficiency": round(eta, 3),
        "spacing_m": spacing,
        "spacing_ratio": round(spacing / diameter, 2),
        "group_q_ult_kn": round(group_q_ult, 2),
        "group_q_all_kn": round(group_q_all, 2),
    }
