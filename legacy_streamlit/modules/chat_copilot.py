"""
chat_copilot.py
GeoCopilot — Professional Geotechnical Engineering Workspace Assistant
Designed for GeoFoundation suite with engineering consulting UI/UX standards.
"""

import html
import re
from typing import Any, Dict, List, Optional
import pandas as pd
import streamlit as st


# -----------------------------------------------------------------------------
# CSS Styling: Professional Geotechnical Engineering Workspace
# -----------------------------------------------------------------------------
GEOCOPILOT_CSS = """
<style>
/* GeoCopilot Container */
.geocopilot-wrapper {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    color: #1E293B;
}

/* Header Section */
.geocopilot-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: linear-gradient(135deg, #0F172A 0%, #1E3A8A 100%);
    color: #FFFFFF;
    padding: 20px 24px;
    border-radius: 10px;
    margin-bottom: 20px;
    box-shadow: 0 4px 12px rgba(15, 23, 42, 0.12);
    border: 1px solid #1E293B;
}

.geocopilot-header-brand {
    display: flex;
    align-items: center;
    gap: 16px;
}

.geocopilot-icon-badge {
    width: 48px;
    height: 48px;
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}

.geocopilot-icon-badge svg {
    width: 28px;
    height: 28px;
    fill: none;
    stroke: #E2E8F0;
    stroke-width: 2;
    stroke-linecap: round;
    stroke-linejoin: round;
}

.geocopilot-title-box h3 {
    margin: 0;
    font-size: 1.35rem;
    font-weight: 700;
    letter-spacing: -0.01em;
    color: #FFFFFF !important;
}

.geocopilot-title-box p {
    margin: 3px 0 0 0;
    font-size: 0.85rem;
    color: #CBD5E1;
    font-weight: 400;
}

.geocopilot-status-badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 6px 14px;
    border-radius: 20px;
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 0.02em;
    background: rgba(16, 185, 129, 0.12);
    color: #A7F3D0;
    border: 1px solid rgba(16, 185, 129, 0.35);
}

.geocopilot-status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background-color: #10B981;
    box-shadow: 0 0 8px #10B981;
}

/* Welcome Section */
.geocopilot-welcome-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-left: 4px solid #8D6E63; /* Earth brown accent */
    border-radius: 8px;
    padding: 20px 24px;
    margin-bottom: 22px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}

.geocopilot-welcome-card h4 {
    margin: 0 0 6px 0;
    font-size: 1.15rem;
    font-weight: 700;
    color: #0F172A;
}

.geocopilot-welcome-card p {
    margin: 0;
    font-size: 0.92rem;
    color: #475569;
    line-height: 1.5;
}

/* Quick Access Cards Grid */
.geocopilot-quick-label {
    font-size: 0.82rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #64748B;
    margin-bottom: 10px;
}

.geocopilot-card-btn {
    background: #FFFFFF;
    border: 1px solid #CBD5E1;
    border-radius: 8px;
    padding: 14px 16px;
    text-align: left;
    transition: all 0.2s ease-in-out;
    cursor: pointer;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03);
    height: 100%;
}

.geocopilot-card-btn:hover {
    border-color: #1E3A8A;
    box-shadow: 0 4px 10px rgba(30, 58, 138, 0.08);
    transform: translateY(-2px);
}

.geocopilot-card-icon {
    font-size: 1.1rem;
    color: #8D6E63;
    margin-bottom: 6px;
}

.geocopilot-card-title {
    font-size: 0.9rem;
    font-weight: 600;
    color: #0F172A;
    margin-bottom: 4px;
}

.geocopilot-card-desc {
    font-size: 0.78rem;
    color: #64748B;
    line-height: 1.35;
}

/* Conversation Thread */
.geocopilot-thread-container {
    display: flex;
    flex-direction: column;
    gap: 16px;
    margin-top: 15px;
    margin-bottom: 25px;
}

/* User Message */
.geocopilot-msg-user {
    align-self: flex-end;
    max-width: 82%;
    background: #F1F5F9;
    border: 1px solid #CBD5E1;
    border-radius: 8px 8px 2px 8px;
    padding: 12px 18px;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
}

.geocopilot-msg-user-header {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: #1E3A8A;
    margin-bottom: 6px;
}

.geocopilot-msg-user-content {
    font-size: 0.92rem;
    color: #0F172A;
    line-height: 1.5;
    word-wrap: break-word;
}

/* Assistant Message */
.geocopilot-msg-assistant {
    align-self: flex-start;
    width: 100%;
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-left: 4px solid #1E3A8A; /* Navy blue accent */
    border-radius: 4px 8px 8px 4px;
    padding: 16px 20px;
    box-shadow: 0 2px 6px rgba(15, 23, 42, 0.04);
}

.geocopilot-msg-assistant-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.03em;
    color: #475569;
    margin-bottom: 10px;
    padding-bottom: 6px;
    border-bottom: 1px solid #F1F5F9;
}

.geocopilot-msg-assistant-brand {
    display: flex;
    align-items: center;
    gap: 8px;
    color: #1E3A8A;
}

.geocopilot-msg-assistant-content {
    font-size: 0.93rem;
    color: #1E293B;
    line-height: 1.6;
}

/* Context Banner */
.geocopilot-context-banner {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 6px;
    padding: 8px 16px;
    font-size: 0.8rem;
    color: #475569;
    margin-bottom: 14px;
}

.geocopilot-context-meta {
    display: flex;
    gap: 16px;
    flex-wrap: wrap;
}

.geocopilot-context-item strong {
    color: #0F172A;
}
</style>
"""

# Minimalist Geotechnical SVG Icon (Stratigraphy Borehole Core)
GEOTECH_SVG_ICON = """
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
    <rect x="5" y="2" width="14" height="20" rx="2" stroke="#CBD5E1" stroke-width="1.8" fill="rgba(255,255,255,0.05)"/>
    <line x1="5" y1="7" x2="19" y2="7" stroke="#A1887F" stroke-width="2"/>
    <line x1="5" y1="13" x2="19" y2="13" stroke="#CBD5E1" stroke-width="2"/>
    <line x1="5" y1="18" x2="19" y2="18" stroke="#8D6E63" stroke-width="2"/>
    <circle cx="12" cy="4.5" r="1.2" fill="#60A5FA"/>
    <line x1="9" y1="10" x2="15" y2="10" stroke="#94A3B8" stroke-width="1.5" stroke-dasharray="1 1"/>
    <line x1="8" y1="15.5" x2="16" y2="15.5" stroke="#94A3B8" stroke-width="1.5" stroke-dasharray="1 1"/>
</svg>
"""


# -----------------------------------------------------------------------------
# Quick Access Topics
# -----------------------------------------------------------------------------
QUICK_ACCESS_TOPICS = [
    {
        "id": "stratigrafi",
        "title": "Analisis Stratigrafi Tanah",
        "desc": "Evaluasi profil susunan perlapisan tanah dan sebarannya",
        "prompt": "Lakukan analisis stratigrafi dan evaluasi kondisi perlapisan tanah berdasarkan data titik bor yang aktif.",
    },
    {
        "id": "spt_cpt",
        "title": "Interpretasi Data SPT & CPT",
        "desc": "Korelasi nilai N-SPT/qc dengan konsistensi dan kepadatan",
        "prompt": "Berikan interpretasi konsistensi tanah, estimasi kepadatan relatif, dan profil daya dukung berdasarkan data N-SPT dan qc yang tersedia.",
    },
    {
        "id": "kapasitas_fondasi",
        "title": "Perhitungan Kapasitas Fondasi",
        "desc": "Metodologi Terzaghi, Meyerhof, dan Luciano Decourt",
        "prompt": "Jelaskan metodologi dan evaluasi kapasitas daya dukung fondasi dangkal dan tiang berdasarkan parameter geoteknik saat ini.",
    },
    {
        "id": "standar_geoteknik",
        "title": "Referensi & Standar Geoteknik",
        "desc": "Pedoman SNI 8460:2017 dan literatur geoteknik standar",
        "prompt": "Sebutkan standar dan referensi geoteknik yang relevan (SNI 8460:2017, Terzaghi, Meyerhof, Luciano Decourt) untuk perancangan fondasi.",
    },
]


# -----------------------------------------------------------------------------
# Geotechnical Engineering Response Engine
# -----------------------------------------------------------------------------
def generate_geotechnical_response(
    query: str,
    soil_df: pd.DataFrame,
    project_metadata: Dict[str, Any],
) -> str:
    """
    Formulates a comprehensive, professional geotechnical engineering response
    integrating active borehole stratigraphy, SPT data, and calculation principles.
    """
    q_lower = query.lower()
    borehole_id = project_metadata.get("borehole_id", "BH-01")
    project_name = project_metadata.get("project_name", "Proyek Geoteknik")
    data_kind = project_metadata.get("data_kind", "Data Aktif")
    gwl = project_metadata.get("gwl")

    is_demo = "demonstrasi" in data_kind.lower()
    data_notice = (
        "> [!NOTE]\n"
        "> **Status Data:** Menggunakan data demonstrasi (BH-01) untuk studi/pengujian. "
        "Bukan data penyelidikan lapangan aktual.\n\n"
        if is_demo
        else (
            f"> [!IMPORTANT]\n"
            f"> **Basis Analisis:** Penyelidikan tanah aktual pada titik **{borehole_id}** "
            f"({project_name}).\n\n"
        )
    )

    has_data = not soil_df.empty and pd.to_numeric(soil_df.get("depth_to", []), errors="coerce").gt(0).any()

    # Topic A: Stratigraphy & Soil Layers
    if any(k in q_lower for k in ["stratigrafi", "lapisan", "profil tanah", "susunan tanah"]):
        if not has_data:
            return (
                f"### Analisis Stratigrafi Tanah\n\n"
                f"Data log titik bor belum diterapkan pada proyek ini. Silakan unggah laporan PDF atau lengkapi tabel pada tab **Data Log Tanah** terlebih dahulu."
            )

        layers_md = []
        for idx, row in soil_df.iterrows():
            z1 = float(row.get("depth_from", 0.0))
            z2 = float(row.get("depth_to", 0.0))
            stype = row.get("soil_type", "Tanah")
            desc = row.get("description", "-")
            nspt = row.get("n_spt", "-")
            gamma = row.get("gamma", "-")
            c = row.get("cohesion", "-")
            phi = row.get("friction_angle", "-")
            layers_md.append(
                f"| {idx+1} | {z1:.2f} – {z2:.2f} m | **{stype}** | {nspt} | {gamma} | {c} | {phi}° | {desc} |"
            )

        gwl_str = f"{gwl:.2f} m di bawah muka tanah" if gwl is not None else "Belum tercantum/teridentifikasi"
        total_depth = float(soil_df["depth_to"].max())

        return (
            f"### 📋 Evaluasi Stratigrafi Tanah — Titik Bor {borehole_id}\n\n"
            f"{data_notice}"
            f"Berdasarkan penampang log pemboran hingga kedalaman **{total_depth:.2f} m**, diperoleh stratigrafi berikut:\n\n"
            f"| No | Kedalaman (m) | Klasifikasi | N-SPT | $\\gamma$ (kN/m³) | $c$ (kPa) | $\\phi$ (°) | Deskripsi Lapisan |\n"
            f"|:--:|:-------------:|:-----------:|:-----:|:----------------:|:---------:|:----------:|:------------------|\n"
            + "\n".join(layers_md) + "\n\n"
            f"**Catatan Hidrologi Geoteknik:**\n"
            f"- Muka Air Tanah (MAT): **{gwl_str}**.\n"
            f"- Fluktuasi muka air tanah harus diperhitungkan dalam evaluasi tegangan efektif ($\\sigma'_v$) "
            f"dan potensi penurunan daya dukung akibat gaya apung (buoyancy)."
        )

    # Topic B: SPT & CPT Interpretation
    elif any(k in q_lower for k in ["spt", "cpt", "sondir", "konsistensi", "kepadatan", "n-value"]):
        if not has_data:
            return (
                "### Interpretasi Data N-SPT dan CPT\n\n"
                "Data penetrasi belum tersedia. Masukkan data log bor untuk mendapatkan evaluasi konsistensi otomatis."
            )

        rows_analysis = []
        for idx, row in soil_df.iterrows():
            nspt_val = row.get("n_spt")
            stype = str(row.get("soil_type", "")).lower()
            z_range = f"{float(row.get('depth_from', 0)):.1f} – {float(row.get('depth_to', 0)):.1f} m"
            
            if pd.isna(nspt_val):
                consistency = "Tidak ada data N-SPT"
            else:
                n = float(nspt_val)
                if any(w in stype for w in ["clay", "lempung", "silt", "lanau"]):
                    if n < 2:
                        consistency = "Sangat Lunak (Very Soft, $c_u < 12$ kPa)"
                    elif n <= 4:
                        consistency = "Lunak (Soft, $c_u \\approx 12 - 25$ kPa)"
                    elif n <= 8:
                        consistency = "Sedang (Medium Stiff, $c_u \\approx 25 - 50$ kPa)"
                    elif n <= 15:
                        consistency = "Kaku (Stiff, $c_u \\approx 50 - 100$ kPa)"
                    elif n <= 30:
                        consistency = "Sangat Kaku (Very Stiff, $c_u \\approx 100 - 200$ kPa)"
                    else:
                        consistency = "Keras (Hard, $c_u > 200$ kPa)"
                else:
                    if n < 4:
                        consistency = "Sangat Lepas (Very Loose, $D_r < 15\\%$)"
                    elif n <= 10:
                        consistency = "Lepas (Loose, $D_r \\approx 15 - 35\\%$)"
                    elif n <= 30:
                        consistency = "Kepadatan Sedang (Medium Dense, $D_r \\approx 35 - 65\\%$)"
                    elif n <= 50:
                        consistency = "Padat (Dense, $D_r \\approx 65 - 85\\%$)"
                    else:
                        consistency = "Sangat Padat (Very Dense, $D_r > 85\\%$)"

            rows_analysis.append(f"- **Kedalaman {z_range}** ({row.get('soil_type', 'Tanah')}): N-SPT = `{nspt_val}` → **{consistency}**")

        return (
            f"### 🔬 Evaluasi Tahanan Penetrasi Standar (N-SPT) & Konsistensi Tanah\n\n"
            f"{data_notice}"
            f"Berdasarkan korelasi empiris Terzaghi & Peck (1967) serta SNI 8460:2017:\n\n"
            + "\n".join(rows_analysis) + "\n\n"
            f"#### Rekomendasi Pemilihan Lapisan Pendukung Fondasi:\n"
            f"1. Lapisan tanah dengan N-SPT < 10 tidak disarankan sebagai lapisan pendukung utama fondasi dangkal "
            f"karena risiko penurunan diferensial (differential settlement).\n"
            f"2. Lapisan tanah keras/padat (N-SPT ≥ 30) sangat ideal sebagai lapisan tumpuan ujung fondasi tiang pancang/bor."
        )

    # Topic C: Foundation Calculation Methodology & Active Results
    elif any(k in q_lower for k in ["fondasi", "kapasitas", "daya dukung", "terzaghi", "meyerhof", "decourt", "bearing", "beban", "penurunan"]):
        shallow_res = project_metadata.get("shallow_res")
        pile_res = project_metadata.get("pile_res")
        group_res = project_metadata.get("group_res")

        active_calc_summary = ""
        if shallow_res or pile_res:
            active_calc_summary += "\n#### 📊 Hasil Perhitungan Desain Fondasi Aktif:\n\n"
            if shallow_res:
                sf_status = "AMAN" if shallow_res.get("is_safe") else "TIDAK AMAN"
                active_calc_summary += (
                    f"**Fondasi Dangkal ({shallow_res.get('footing_type', 'Footing')} {shallow_res.get('dimensions', '')}):**\n"
                    f"- Daya Dukung Ultimit ($q_{{ult}}$): `{shallow_res.get('q_ult_kpa', '-')} kPa`\n"
                    f"- Daya Dukung Izin ($q_{{all}}$): `{shallow_res.get('q_all_kpa', '-')} kPa`\n"
                    f"- Tekanan Kontak Terapan ($q_{{terapan}}$): `{shallow_res.get('q_applied_kpa', '-')} kPa`\n"
                    f"- Faktor Keamanan Aktual ($FK$): `{shallow_res.get('actual_sf', '-')} ` ({sf_status}, FK Rencana = {shallow_res.get('required_sf', 3.0)})\n\n"
                )
            if pile_res:
                active_calc_summary += (
                    f"**Fondasi Tiang Tunggal ({pile_res.get('pile_type', 'Pile')} D={pile_res.get('pile_diameter_m', '-')}m, L={pile_res.get('pile_length_m', '-')}m):**\n"
                    f"- Tahanan Ujung ($Q_b$): `{pile_res.get('q_end_bearing_kn', '-')} kN`\n"
                    f"- Tahanan Selimut ($Q_s$): `{pile_res.get('q_shaft_friction_kn', '-')} kN`\n"
                    f"- Kapasitas Ultimit ($Q_{{ult}}$): `{pile_res.get('q_ult_kn', '-')} kN`\n"
                    f"- Kapasitas Izin ($Q_{{izin}}$): `{pile_res.get('q_all_dual_sf_kn', '-')} kN`\n\n"
                )
            if group_res:
                active_calc_summary += (
                    f"**Kelompok Tiang ({group_res.get('total_piles', '-')} tiang, jarak {group_res.get('spacing_m', '-')}m):**\n"
                    f"- Efisiensi Kelompok ($\\eta$ Converse-Labarre): `{group_res.get('efficiency', 0)*100:.1f} %`\n"
                    f"- Kapasitas Izin Kelompok ($Q_{{g,izin}}$): `{group_res.get('group_q_all_kn', '-')} kN`\n\n"
                )

        return (
            f"### 📐 Metodologi & Evaluasi Kapasitas Daya Dukung Fondasi\n\n"
            f"{data_notice}"
            f"GeoFoundation menerapkan formulasi analitis geoteknik standar:\n\n"
            f"#### 1. Fondasi Dangkal (Metode Meyerhof & Terzaghi)\n"
            f"Persamaan umum kapasitas daya dukung ultimit ($q_{{ult}}$):\n\n"
            f"$$q_{{ult}} = c \\cdot N_c \\cdot s_c \\cdot d_c + q' \\cdot N_q \\cdot s_q \\cdot d_q + \\frac{{1}}{{2}} \\cdot \\gamma' \\cdot B \\cdot N_\\gamma \\cdot s_\\gamma \\cdot d_\\gamma$$\n\n"
            f"- **$c$**: Kohesi tanah efektif (kPa)\n"
            f"- **$q'$**: Tegangan overburden efektif di dasar fondasi $= \\gamma \\cdot D_f$ (disesuaikan dengan posisi MAT)\n"
            f"- **$\\gamma'$**: Berat isi efektif tanah di bawah dasar fondasi\n"
            f"- **$N_c, N_q, N_\\gamma$**: Faktor daya dukung fungsi $\\phi$\n"
            f"- **$s_c, s_q, s_\\gamma$** & **$d_c, d_q, d_\\gamma$**: Faktor bentuk dan kedalaman\n"
            f"- **Daya dukung izin:** $q_{{all}} = \\frac{{q_{{ult}}}}{{FS}}$ ($FS \\ge 3.0$)\n\n"
            f"#### 2. Fondasi Tiang (Metode Meyerhof 1976 & Luciano Decourt 1996)\n"
            f"Kapasitas ultimit tiang tunggal ($Q_{{ult}}$):\n\n"
            f"$$Q_{{ult}} = Q_b + Q_s = q_b \\cdot A_b + \\sum (f_{{si}} \\cdot A_{{si}})$$\n\n"
            f"- **Tahanan Ujung ($Q_b$)**: $q_b = 40 \\cdot N_{{SPT}} \\cdot (L/D) \\le 400 \\cdot N_{{SPT}}$ (kPa) [Meyerhof]\n"
            f"- **Tahanan Selimut ($Q_s$)**: $f_{{si}} = 2.0 \\cdot N_{{SPT}}$ (pasir); $f_{{si}} = \\alpha \\cdot c_u$ (lempung)\n"
            f"- **Efisiensi Kelompok Tiang**: Dihitung dengan rumus **Converse-Labarre** untuk konfigurasi baris $\\times$ kolom."
            f"{active_calc_summary}"
        )

    # Topic D: Standards & References
    elif any(k in q_lower for k in ["standar", "sni", "referensi", "acuan", "peraturan", "pedoman"]):
        return (
            f"### 📚 Standar dan Acuan Normatif Perancangan Geoteknik\n\n"
            f"GeoFoundation mengacu pada pedoman standar industri konstruksi dan geoteknik:\n\n"
            f"1. **SNI 8460:2017** — *Persyaratan Perancangan Geoteknik*\n"
            f"   - Ketentuan penyelidikan tanah di lapangan dan laboratorium.\n"
            f"   - Faktor keamanan minimum untuk fondasi dangkal ($FS \\ge 3.0$) dan fondasi dalam ($FS \\ge 2.5 - 3.0$).\n\n"
            f"2. **SNI 1726:2019** — *Tata Cara Perencanaan Ketahanan Gempa untuk Struktur Gedung dan Non Gedung*\n"
            f"   - Klasifikasi situs tanah ($S_A, S_B, S_C, S_D, S_E, S_F$) berdasarkan $\\bar{{N}}_{{SPT}}$ kedalaman 30 m.\n\n"
            f"3. **Meyerhof, G.G. (1963 & 1976)**\n"
            f"   - *Some Recent Research on the Bearing Capacity of Foundations*, Canadian Geotechnical Journal.\n"
            f"   - Korelasi empiris kapasitas fondasi tiang dari data Standard Penetration Test (SPT).\n\n"
            f"4. **Decourt, L. (1996)**\n"
            f"   - *Prediction of Load-Settlement Relationships for Foundations on the Basis of the SPT-T*, Cicero Veloso.\n\n"
            f"5. **Terzaghi, K., Peck, R.B., & Mesri, G. (1996)**\n"
            f"   - *Soil Mechanics in Engineering Practice*, John Wiley & Sons."
        )

    # General Geotechnical Consultation
    else:
        gwl_info = f"{gwl:.2f} m" if gwl is not None else "tidak tercantum"
        return (
            f"### 🧭 Rekomendasi Teknis GeoCopilot\n\n"
            f"{data_notice}"
            f"Terkait pertanyaan Anda: *\"{query}\"*\n\n"
            f"Pada titik bor **{borehole_id}** ({project_name}) dengan kedalaman muka air tanah **{gwl_info}**:\n\n"
            f"1. **Verifikasi Parameter Input:** Pastikan nilai kohesi ($c$), sudut geser dalam ($\\phi$), dan berat isi ($\\gamma$) telah sesuai dengan hasil uji triaksial/direct shear laboratorium atau korelasi N-SPT yang telah dikoreksi ($N_{{60}}$).\n"
            f"2. **Analisis Fondasi Dangkal:** Dapat diuji pada tab **Fondasi Dangkal** untuk mendapatkan nilai $q_{{ult}}$ dan $q_{{all}}$ beserta verifikasi tegangan kontak.\n"
            f"3. **Analisis Fondasi Dalam:** Evaluasi penanaman tiang hingga menyentuh lapisan tanah keras (N-SPT > 30) pada tab **Fondasi Tiang** untuk mengoptimalkan tahanan ujung ($Q_b$) dan friksi ($Q_s$).\n\n"
            f"*Silakan pilih salah satu kartu akses cepat di atas atau tanyakan aspek spesifik lainnya terkait mekanika tanah dan rekayasa fondasi.*"
        )


# -----------------------------------------------------------------------------
# Main Render Function for Streamlit
# -----------------------------------------------------------------------------
def render_chat_copilot(
    soil_df: pd.DataFrame,
    project_metadata: Dict[str, Any],
) -> None:
    """
    Renders the professional GeoCopilot workspace inside GeoFoundation.
    """
    # Inject CSS
    st.markdown(GEOCOPILOT_CSS, unsafe_allow_html=True)

    # Initialize Session State Messages
    if "copilot_messages" not in st.session_state:
        st.session_state.copilot_messages = []

    # Initialize Session State Prompt Trigger (for quick access cards)
    if "copilot_pending_prompt" not in st.session_state:
        st.session_state.copilot_pending_prompt = None

    borehole_id = project_metadata.get("borehole_id", "BH-01")
    project_name = project_metadata.get("project_name", "Proyek Geoteknik")
    data_kind = project_metadata.get("data_kind", "Data Aktif")
    is_demo = "demonstrasi" in data_kind.lower()

    # 1. Professional Header
    system_status = "Sistem Siap • Data Demonstrasi" if is_demo else f"Sistem Siap • Terhubung ke {borehole_id}"
    st.markdown(f"""
    <div class="geocopilot-wrapper">
        <div class="geocopilot-header">
            <div class="geocopilot-header-brand">
                <div class="geocopilot-icon-badge">
                    {GEOTECH_SVG_ICON}
                </div>
                <div class="geocopilot-title-box">
                    <h3>GeoCopilot</h3>
                    <p>Geotechnical Engineering Assistant & Foundation Advisory</p>
                </div>
            </div>
            <div class="geocopilot-status-badge">
                <div class="geocopilot-status-dot"></div>
                {html.escape(system_status)}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 2. Context Status Banner
    gwl_val = project_metadata.get("gwl")
    gwl_display = f"{gwl_val:.2f} m" if gwl_val is not None else "Belum ditentukan"
    layer_count = len(soil_df) if not soil_df.empty else 0
    max_depth = f"{float(soil_df['depth_to'].max()):.2f} m" if not soil_df.empty and 'depth_to' in soil_df else "0 m"

    st.markdown(f"""
    <div class="geocopilot-context-banner">
        <div class="geocopilot-context-meta">
            <div class="geocopilot-context-item">Titik Bor: <strong>{html.escape(str(borehole_id))}</strong></div>
            <div class="geocopilot-context-item">Proyek: <strong>{html.escape(str(project_name))}</strong></div>
            <div class="geocopilot-context-item">Lapisan Tanah: <strong>{layer_count} lapisan ({max_depth})</strong></div>
            <div class="geocopilot-context-item">Muka Air Tanah (MAT): <strong>{gwl_display}</strong></div>
        </div>
        <div style="font-size: 0.76rem; color: #64748B;">SNI 8460:2017 Standard</div>
    </div>
    """, unsafe_allow_html=True)

    # 3. Welcome Section
    st.markdown("""
    <div class="geocopilot-welcome-card">
        <h4>Ruang Konsultasi Geoteknik</h4>
        <p>Analisis data tanah, evaluasi parameter, dan perencanaan fondasi sesuai prinsip mekanika tanah dan standar rekayasa geoteknik.</p>
    </div>
    """, unsafe_allow_html=True)

    # 4. Quick Access Cards
    st.markdown('<div class="geocopilot-quick-label">⚡ Kartu Akses Cepat Analisis</div>', unsafe_allow_html=True)
    cols = st.columns(4)
    for idx, topic in enumerate(QUICK_ACCESS_TOPICS):
        with cols[idx]:
            card_html = f"""
            <div class="geocopilot-card-btn">
                <div class="geocopilot-card-icon">▸</div>
                <div class="geocopilot-card-title">{html.escape(topic['title'])}</div>
                <div class="geocopilot-card-desc">{html.escape(topic['desc'])}</div>
            </div>
            """
            st.markdown(card_html, unsafe_allow_html=True)
            if st.button(f"Pilih {topic['title']}", key=f"btn_quick_{topic['id']}", use_container_width=True):
                st.session_state.copilot_pending_prompt = topic["prompt"]

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    # Handle pending prompt from quick access cards
    active_prompt = None
    if st.session_state.copilot_pending_prompt:
        active_prompt = st.session_state.copilot_pending_prompt
        st.session_state.copilot_pending_prompt = None

    # Chat Input Box
    user_input = st.chat_input(
        placeholder="Tanyakan analisis stratigrafi, evaluasi parameter tanah, atau perhitungan fondasi..."
    )

    if user_input:
        active_prompt = user_input

    # 5. Conversation Thread Display
    if st.session_state.copilot_messages:
        col_thread, col_act = st.columns([0.88, 0.12])
        with col_act:
            if st.button("🗑️ Bersihkan", help="Hapus riwayat percakapan konsultasi", use_container_width=True):
                st.session_state.copilot_messages = []
                st.rerun()

        for msg in st.session_state.copilot_messages:
            if msg["role"] == "user":
                st.markdown(f"""
                <div class="geocopilot-msg-user">
                    <div class="geocopilot-msg-user-header">
                        <span>👤 Insinyur Geoteknik</span>
                    </div>
                    <div class="geocopilot-msg-user-content">
                        {html.escape(msg['content'])}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="geocopilot-msg-assistant">
                    <div class="geocopilot-msg-assistant-header">
                        <div class="geocopilot-msg-assistant-brand">
                            <span>🧭 GeoCopilot • Engineering Assistant</span>
                        </div>
                        <span>Konsultasi Teknis</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                # Render markdown content (supports equations, markdown tables, code)
                st.markdown(msg["content"])

    # 6. Process New Message
    if active_prompt:
        # Append user message
        st.session_state.copilot_messages.append({
            "role": "user",
            "content": active_prompt
        })

        # Display user message immediately
        st.markdown(f"""
        <div class="geocopilot-msg-user">
            <div class="geocopilot-msg-user-header">
                <span>👤 Insinyur Geoteknik</span>
            </div>
            <div class="geocopilot-msg-user-content">
                {html.escape(active_prompt)}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Generate response with spinner
        with st.spinner("GeoCopilot sedang menganalisis data geoteknik dan merumuskan respons rekayasa..."):
            response_text = generate_geotechnical_response(
                query=active_prompt,
                soil_df=soil_df,
                project_metadata=project_metadata,
            )

        # Append assistant response
        st.session_state.copilot_messages.append({
            "role": "assistant",
            "content": response_text
        })

        # Display assistant message
        st.markdown("""
        <div class="geocopilot-msg-assistant">
            <div class="geocopilot-msg-assistant-header">
                <div class="geocopilot-msg-assistant-brand">
                    <span>🧭 GeoCopilot • Engineering Assistant</span>
                </div>
                <span>Konsultasi Teknis</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown(response_text)
        st.rerun()
