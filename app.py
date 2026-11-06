"""
app.py
GeoFoundation — Interactive Geotechnical Foundation Engineering Application
Developed for Civil & Geotechnical Engineering (APLIKOM).
Analyzes borehole logs, soil stratigraphy, N-SPT profiles,
and computes shallow & deep foundation bearing capacity.
"""

import hashlib
import io
import os
import streamlit as st
import pandas as pd
import numpy as np

# Import custom geotechnical modules
from modules.pdf_reader import (
    parse_soil_investigation_pdf,
    get_sample_soil_data,
    get_empty_soil_data,
    standardize_borehole_table,
)
from modules.soil_visualization import (
    create_interactive_soil_profile,
    create_matplotlib_soil_profile,
)
from modules.foundation_calculation import (
    calculate_shallow_foundation,
    calculate_single_pile_capacity,
    calculate_pile_capacity_depth_profile,
    calculate_pile_group,
    get_bearing_capacity_factors,
)
from modules.chat_copilot import render_chat_copilot

# Page configuration
st.set_page_config(
    page_title="GeoFoundation — Analisis Geoteknik",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        color: #1A237E;
        margin-bottom: 0px;
    }
    .sub-title {
        font-size: 1.05rem;
        color: #455A64;
        margin-bottom: 20px;
    }
    .metric-card {
        background: #F8F9FA;
        border-radius: 8px;
        padding: 16px;
        border-left: 5px solid #1E88E5;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    }
    .status-pass {
        color: #2E7D32;
        font-weight: bold;
        background: #E8F5E9;
        padding: 4px 10px;
        border-radius: 4px;
        display: inline-block;
    }
    .status-fail {
        color: #C62828;
        font-weight: bold;
        background: #FFEBEE;
        padding: 4px 10px;
        border-radius: 4px;
        display: inline-block;
    }
</style>
""", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# Sidebar: Project Info & Soil Data Management
# -----------------------------------------------------------------------------
logo_path = os.path.join(os.path.dirname(__file__), "assets", "logo.png")
if not os.path.exists(logo_path):
    logo_path = "assets/logo.png"

if os.path.exists(logo_path):
    st.sidebar.image(logo_path, width=72)

st.sidebar.title("GeoFoundation")
st.sidebar.caption("Aplikasi Analisis dan Perancangan Geoteknik")
st.sidebar.divider()

st.sidebar.subheader("📂 Sumber Data Penyelidikan Tanah")
data_source = st.sidebar.radio(
    "Pilih Sumber Data:",
    ["Data Contoh (BH-01)", "Unggah Laporan PDF", "Unggah CSV/Excel", "Sunting Tabel Manual"],
)

st.sidebar.divider()
st.sidebar.subheader("📌 Informasi Proyek")
is_demo_source = data_source == "Data Contoh (BH-01)"
source_key = {
    "Data Contoh (BH-01)": "demonstrasi",
    "Unggah Laporan PDF": "pdf",
    "Unggah CSV/Excel": "berkas",
    "Sunting Tabel Manual": "manual",
}[data_source]
project_name = st.sidebar.text_input(
    "Nama Proyek",
    value="Proyek Teknik Sipil" if is_demo_source else "",
    key=f"project_name_{source_key}",
)
investigation_location = st.sidebar.text_input(
    "Lokasi Penyelidikan", value="", key=f"location_{source_key}"
)
borehole_id = st.sidebar.text_input(
    "ID Titik Bor", value="BH-01" if is_demo_source else "", key=f"borehole_{source_key}"
)
engineer_name = st.sidebar.text_input(
    "Nama Insinyur Geoteknik",
    value="Insinyur Teknik Sipil" if is_demo_source else "",
    key=f"engineer_{source_key}",
)
cached_pdf_metadata = st.session_state.get("pdf_metadata", {})
gwl_default = (
    2.5 if is_demo_source
    else cached_pdf_metadata.get("ground_water_level") if source_key == "pdf"
    else None
)
gwl_input = st.sidebar.number_input(
    "Muka Air Tanah (MAT) [m di bawah permukaan]",
    min_value=0.0,
    max_value=50.0,
    value=gwl_default,
    step=0.5,
    key=f"gwl_{source_key}",
    help="Nilai kosong berarti muka air tanah tidak tercantum atau belum ditentukan.",
)

# Initialize separate active and preview datasets.
if "soil_df" not in st.session_state:
    st.session_state.soil_df = (
        get_sample_soil_data()
        if data_source == "Data Contoh (BH-01)"
        else get_empty_soil_data()
    )
if "soil_preview_df" not in st.session_state:
    st.session_state.soil_preview_df = st.session_state.soil_df.copy()
if "soil_data_kind" not in st.session_state:
    st.session_state.soil_data_kind = (
        "demonstrasi" if data_source == "Data Contoh (BH-01)" else "belum tersedia"
    )
if "selected_data_source" not in st.session_state:
    st.session_state.selected_data_source = "Data Contoh (BH-01)"

if st.session_state.selected_data_source != data_source:
    if data_source == "Data Contoh (BH-01)":
        st.session_state.soil_df = get_sample_soil_data()
        st.session_state.soil_preview_df = st.session_state.soil_df.copy()
        st.session_state.soil_data_kind = "demonstrasi"
    elif data_source in {"Unggah Laporan PDF", "Unggah CSV/Excel"}:
        st.session_state.soil_df = get_empty_soil_data()
        st.session_state.soil_preview_df = get_empty_soil_data()
        st.session_state.soil_data_kind = "belum tersedia"
        st.session_state.parsed_pdf_hash = None
        st.session_state.applied_pdf_hash = None
        st.session_state.pdf_metadata = {}
    elif data_source == "Sunting Tabel Manual":
        st.session_state.soil_preview_df = st.session_state.soil_df.copy()
    st.session_state.selected_data_source = data_source

pdf_diagnostics = None

if data_source == "Data Contoh (BH-01)":
    st.sidebar.info("Data bawaan yang dimuat melalui tombol di bawah hanya untuk demonstrasi, bukan hasil penyelidikan tanah di lapangan.")
    if st.sidebar.button("🔄 Muat Ulang Data Contoh BH-01"):
        st.session_state.soil_df = get_sample_soil_data()
        st.session_state.soil_preview_df = st.session_state.soil_df.copy()
        st.session_state.soil_data_kind = "demonstrasi"
        st.sidebar.success("Data contoh berhasil dimuat ulang.")

elif data_source == "Unggah Laporan PDF":
    uploaded_pdf = st.sidebar.file_uploader("Unggah Laporan Penyelidikan Tanah (PDF)", type=["pdf"], key="pdf_upload")
    if uploaded_pdf is not None:
        pdf_bytes = uploaded_pdf.getvalue()
        pdf_hash = hashlib.sha256(pdf_bytes).hexdigest()
        if st.session_state.get("parsed_pdf_hash") != pdf_hash:
            st.session_state.soil_df = get_empty_soil_data()
            st.session_state.soil_data_kind = "belum tersedia"
            st.session_state.applied_pdf_hash = None
            with st.spinner("Mengekstrak teks, tabel, dan data geoteknik dari PDF..."):
                try:
                    extracted_df, meta = parse_soil_investigation_pdf(pdf_bytes)
                    st.session_state.soil_preview_df = extracted_df
                    st.session_state.pdf_metadata = meta
                    st.session_state.pdf_parse_error = None
                except Exception as error:
                    st.session_state.soil_preview_df = get_empty_soil_data()
                    st.session_state.pdf_metadata = {}
                    st.session_state.pdf_parse_error = str(error)
                st.session_state.parsed_pdf_hash = pdf_hash

        meta = st.session_state.get("pdf_metadata", {})
        pdf_diagnostics = meta.get("diagnostics")
        if st.session_state.get("pdf_parse_error"):
            st.sidebar.error(f"PDF tidak dapat diproses: {st.session_state.pdf_parse_error}")
        elif not st.session_state.soil_preview_df.empty:
            if st.session_state.get("applied_pdf_hash") == pdf_hash:
                st.sidebar.success(f"Data PDF aktif: {len(st.session_state.soil_df)} baris telah diterapkan.")
            else:
                st.sidebar.success(
                    f"Ditemukan {len(st.session_state.soil_preview_df)} baris data. "
                    "Periksa dan sunting tabel sebelum menerapkan untuk analisis."
                )
        else:
            diagnostic_message = pdf_diagnostics.get("message", "Data tanah tidak ditemukan.") if pdf_diagnostics else "Data tanah tidak ditemukan."
            st.sidebar.warning(diagnostic_message)

        if pdf_diagnostics:
            with st.sidebar.expander("Diagnostik ekstraksi PDF"):
                field_labels = {
                    "depth_from": "Kedalaman awal",
                    "depth_to": "Kedalaman akhir",
                    "soil_type": "Klasifikasi tanah",
                    "description": "Deskripsi tanah",
                    "n_spt": "N-SPT",
                    "qc": "qc sondir",
                    "gamma": "Berat isi",
                    "cohesion": "Kohesi",
                    "friction_angle": "Sudut geser dalam",
                    "water_content_pct": "Kadar air",
                    "liquid_limit_pct": "Batas cair",
                    "plastic_limit_pct": "Batas plastis",
                    "specific_gravity": "Berat jenis",
                    "void_ratio": "Angka pori",
                    "unconfined_compressive_strength_kpa": "Kuat tekan bebas",
                }
                metadata_labels = {
                    "project_name": "Nama proyek",
                    "location": "Lokasi",
                    "borehole_id": "Nomor titik bor/sondir",
                    "ground_water_level": "Muka air tanah",
                }
                st.write(f"Halaman: {pdf_diagnostics['page_count']}")
                st.write(f"Halaman dengan teks: {pdf_diagnostics['text_pages']}")
                st.write(f"Jumlah karakter teks: {pdf_diagnostics['text_character_count']}")
                st.write(f"Tabel terdeteksi: {pdf_diagnostics['tables_detected']}")
                st.write(f"Halaman tabel: {pdf_diagnostics['table_pages']}")
                extracted_labels = [field_labels.get(field, field) for field in pdf_diagnostics["extracted_fields"]]
                st.write(f"Data ditemukan: {extracted_labels or 'belum ada'}")
                if pdf_diagnostics["missing_metadata"]:
                    missing_labels = [metadata_labels.get(field, field) for field in pdf_diagnostics["missing_metadata"]]
                    st.info(f"Informasi tidak tercantum: {', '.join(missing_labels)}")
                if pdf_diagnostics["ocr_required_pages"]:
                    st.warning(pdf_diagnostics["ocr_message"])
                if pdf_diagnostics["fitz_error"]:
                    st.caption(f"Diagnostik teks: {pdf_diagnostics['fitz_error']}")
                if pdf_diagnostics["pdfplumber_error"]:
                    st.caption(f"Diagnostik tabel: {pdf_diagnostics['pdfplumber_error']}")

        project_name = project_name or meta.get("project_name")
        investigation_location = investigation_location or meta.get("location")
        borehole_id = borehole_id or meta.get("borehole_id")
        extracted_gwl = meta.get("ground_water_level")
        if gwl_input is None and extracted_gwl is not None:
            gwl_input = float(extracted_gwl)
    else:
        if st.session_state.get("parsed_pdf_hash") is not None:
            st.session_state.soil_df = get_empty_soil_data()
            st.session_state.soil_preview_df = get_empty_soil_data()
            st.session_state.soil_data_kind = "belum tersedia"
            st.session_state.parsed_pdf_hash = None
            st.session_state.applied_pdf_hash = None
            st.session_state.pdf_metadata = {}
        st.sidebar.info("Unggah PDF untuk memulai ekstraksi. Data aktif sebelumnya tidak digunakan pada sumber ini.")

elif data_source == "Unggah CSV/Excel":
    uploaded_file = st.sidebar.file_uploader("Unggah Data Log Pengeboran", type=["csv", "xlsx", "xls"])
    if uploaded_file is not None:
        try:
            if uploaded_file.name.lower().endswith(".csv"):
                df_raw = pd.read_csv(uploaded_file)
            else:
                df_raw = pd.read_excel(uploaded_file)
            cleaned = standardize_borehole_table(df_raw)
            if not cleaned.empty:
                st.session_state.soil_df = cleaned
                st.session_state.soil_preview_df = cleaned.copy()
                st.session_state.soil_data_kind = "berkas CSV/Excel"
                st.sidebar.success(f"Berhasil mengimpor {len(cleaned)} lapisan tanah.")
            else:
                st.session_state.soil_df = get_empty_soil_data()
                st.session_state.soil_preview_df = get_empty_soil_data()
                st.sidebar.warning("Kolom kedalaman dan data tanah tidak dikenali. Data contoh tidak digunakan sebagai pengganti.")
        except Exception as e:
            st.session_state.soil_df = get_empty_soil_data()
            st.session_state.soil_preview_df = get_empty_soil_data()
            st.sidebar.error(f"Terjadi kesalahan saat membaca berkas: {e}")


# -----------------------------------------------------------------------------
# Main Navigation Tabs
# -----------------------------------------------------------------------------
project_name = project_name or "Tidak tercantum"
investigation_location = investigation_location or "Tidak tercantum"
borehole_id = borehole_id or "Tidak tercantum"
engineer_name = engineer_name or "Tidak tercantum"
st.markdown('<div class="main-title">🏗️ GeoFoundation — Analisis Fondasi</div>', unsafe_allow_html=True)
st.markdown(f'<div class="sub-title">Proyek: <b>{project_name}</b> | Lokasi: <b>{investigation_location}</b> | Titik Bor: <b>{borehole_id}</b> | Insinyur: <b>{engineer_name}</b></div>', unsafe_allow_html=True)

tab_log, tab_strat, tab_shallow, tab_deep, tab_copilot, tab_export = st.tabs([
    "📋 Data Log Tanah",
    "📊 Stratigrafi & Profil N-SPT",
    "🧱 Fondasi Dangkal",
    "🔩 Fondasi Tiang",
    "💬 ChatCopilot",
    "📑 Ringkasan Laporan"
])


# =============================================================================
# TAB 1: Soil Log Data Editor
# =============================================================================
with tab_log:
    st.subheader("Tabel Stratigrafi Titik Bor dan Parameter Tanah")
    st.markdown(
        "Tinjau dan sesuaikan rentang kedalaman lapisan, klasifikasi tanah, nilai pukulan N-SPT, "
        "kohesi ($c$), sudut geser dalam ($\\phi$), dan berat isi ($\\gamma$)."
    )

    if data_source == "Unggah Laporan PDF":
        st.info("Tabel ini adalah pratinjau ekstraksi PDF. Terapkan data setelah memeriksa dan menyuntingnya.")
        editor_df = st.session_state.soil_preview_df
    else:
        editor_df = st.session_state.soil_df

    edited_df = st.data_editor(
        editor_df,
        num_rows="dynamic",
        width="stretch",
        column_config={
            "depth_from": st.column_config.NumberColumn("Kedalaman Awal (m)", min_value=0.0, step=0.5, format="%.2f"),
            "depth_to": st.column_config.NumberColumn("Kedalaman Akhir (m)", min_value=0.1, step=0.5, format="%.2f"),
            "soil_type": st.column_config.TextColumn("Klasifikasi Tanah"),
            "description": st.column_config.TextColumn("Deskripsi Visual", width="large"),
            "n_spt": st.column_config.NumberColumn("N-SPT", min_value=0, max_value=100, step=1),
            "qc": st.column_config.NumberColumn("qc", min_value=0.0, step=0.01, format="%.3f"),
            "qc_unit": st.column_config.TextColumn("Satuan qc"),
            "gamma": st.column_config.NumberColumn("γ (kN/m³)", min_value=10.0, max_value=25.0, step=0.1, format="%.1f"),
            "cohesion": st.column_config.NumberColumn("c (kPa)", min_value=0.0, max_value=500.0, step=1.0, format="%.1f"),
            "friction_angle": st.column_config.NumberColumn("φ (°)", min_value=0.0, max_value=50.0, step=0.5, format="%.1f"),
            "water_content_pct": st.column_config.NumberColumn("Kadar Air (%)", min_value=0.0, step=0.1, format="%.1f"),
            "liquid_limit_pct": st.column_config.NumberColumn("Batas Cair (%)", min_value=0.0, step=0.1, format="%.1f"),
            "plastic_limit_pct": st.column_config.NumberColumn("Batas Plastis (%)", min_value=0.0, step=0.1, format="%.1f"),
            "specific_gravity": st.column_config.NumberColumn("Berat Jenis (Gs)", min_value=0.0, step=0.01, format="%.2f"),
            "void_ratio": st.column_config.NumberColumn("Angka Pori (e)", min_value=0.0, step=0.01, format="%.2f"),
            "unconfined_compressive_strength_kpa": st.column_config.NumberColumn("Kuat Tekan Bebas (kPa)", min_value=0.0, step=1.0, format="%.1f"),
        },
    )
    if data_source == "Unggah Laporan PDF":
        st.session_state.soil_preview_df = edited_df
        apply_pdf_data = st.button(
            "Gunakan Data PDF untuk Analisis",
            disabled=edited_df.empty,
            help="Data PDF tetap menjadi pratinjau sampai tombol ini ditekan.",
        )
        if apply_pdf_data:
            st.session_state.soil_df = edited_df.copy()
            st.session_state.soil_data_kind = "hasil ekstraksi PDF"
            st.session_state.applied_pdf_hash = st.session_state.get("parsed_pdf_hash")
            st.success("Data PDF diterapkan. Lengkapi parameter inti yang masih kosong sebelum analisis.")
    else:
        st.session_state.soil_df = edited_df
        if data_source == "Data Contoh (BH-01)":
            st.session_state.soil_preview_df = edited_df.copy()
        elif data_source == "Sunting Tabel Manual":
            kind_labels = {
                "demonstrasi": "data demonstrasi yang disunting",
                "hasil ekstraksi PDF": "hasil ekstraksi PDF yang disunting",
                "berkas CSV/Excel": "berkas CSV/Excel yang disunting",
            }
            st.session_state.soil_data_kind = kind_labels.get(
                st.session_state.soil_data_kind, "data manual"
            )

    col_info1, col_info2, col_info3 = st.columns(3)
    col_info1.metric("Jumlah Lapisan", len(edited_df))
    max_d = float(edited_df["depth_to"].max()) if not edited_df.empty else 0.0
    col_info2.metric("Kedalaman Penyelidikan", f"{max_d:.2f} m")
    avg_spt = float(edited_df["n_spt"].mean()) if not edited_df.empty else 0.0
    col_info3.metric("Rata-rata N-SPT", f"{avg_spt:.1f}")

active_soil_df = st.session_state.soil_df
if active_soil_df.empty or not pd.to_numeric(active_soil_df["depth_to"], errors="coerce").gt(0).any():
    st.warning("Belum ada data tanah aktif untuk analisis. Unggah PDF, periksa tabel pratinjau, lalu terapkan data; atau pilih data demonstrasi secara terpisah.")
    st.stop()

required_analysis_columns = ["depth_from", "depth_to", "n_spt", "gamma", "cohesion", "friction_angle"]
missing_analysis_columns = [
    column for column in required_analysis_columns
    if column not in active_soil_df or pd.to_numeric(active_soil_df[column], errors="coerce").isna().any()
]
if missing_analysis_columns:
    display_names = {
        "depth_from": "Kedalaman Awal",
        "depth_to": "Kedalaman Akhir",
        "n_spt": "N-SPT",
        "gamma": "Berat Isi",
        "cohesion": "Kohesi",
        "friction_angle": "Sudut Geser Dalam",
    }
    missing_labels = [display_names[column] for column in missing_analysis_columns]
    st.warning(
        "Analisis belum dijalankan karena parameter berikut belum tersedia pada seluruh baris: "
        + ", ".join(missing_labels)
        + ". Lengkapi tabel, lalu terapkan kembali data PDF."
    )
    st.stop()


# =============================================================================
# TAB 2: Stratigraphy & N-SPT Profile Visualization
# =============================================================================
with tab_strat:
    st.subheader("Grafik Stratigrafi dan N-SPT terhadap Kedalaman")
    st.markdown("Profil log titik bor dengan warna lapisan tanah dan kurva tahanan penetrasi.")

    if not st.session_state.soil_df.empty:
        fig_plotly = create_interactive_soil_profile(
            st.session_state.soil_df,
            gwl=gwl_input,
            borehole_id=borehole_id
        )
        st.plotly_chart(fig_plotly, width="stretch")

        with st.expander("📸 Tampilkan Grafik Statis Resolusi Tinggi"):
            fig_mpl = create_matplotlib_soil_profile(
                st.session_state.soil_df,
                gwl=gwl_input,
                borehole_id=borehole_id
            )
            st.pyplot(fig_mpl)
    else:
        st.warning("Data tanah belum tersedia untuk divisualisasikan. Masukkan data pada tab pertama.")


# =============================================================================
# TAB 3: Shallow Foundation (Pondasi Dangkal)
# =============================================================================
with tab_shallow:
    st.subheader("Daya Dukung Fondasi Dangkal")
    st.markdown("Menghitung daya dukung ultimit dan izin dengan metode Meyerhof atau Terzaghi.")

    col_in1, col_in2 = st.columns([1, 1])

    with col_in1:
        st.markdown("##### 📐 Geometri dan Dimensi Fondasi")
        footing_shape = st.selectbox("Bentuk Fondasi", ["Persegi", "Persegi Panjang", "Menerus", "Lingkaran"])
        
        col_w, col_l = st.columns(2)
        width_b = col_w.number_input("Lebar Fondasi B (m)", min_value=0.5, max_value=20.0, value=2.0, step=0.25)
        length_l = col_l.number_input(
            "Panjang Fondasi L (m)",
            min_value=width_b if footing_shape == "Persegi Panjang" else 0.5,
            value=max(width_b, 2.0),
            step=0.25,
            disabled=(footing_shape in ["Persegi", "Menerus", "Lingkaran"])
        )
        depth_df = st.number_input("Kedalaman Fondasi Df (m)", min_value=0.5, max_value=15.0, value=1.5, step=0.25)
        applied_load_p = st.number_input("Beban Aksial Rencana Kolom P (kN)", min_value=0.0, value=350.0, step=25.0)

    with col_in2:
        st.markdown("##### 🔬 Parameter Tanah dan Metode Perhitungan")
        shallow_method = st.selectbox("Metode Perhitungan", ["Meyerhof", "Terzaghi"])
        sf_req = st.slider("Faktor Keamanan Rencana (FK)", min_value=2.0, max_value=4.0, value=3.0, step=0.1)

        # Allow user to autofill soil params from a selected borehole layer
        layer_options = [
            f"Lapisan {i+1}: {r['soil_type']} ({r['depth_from']} - {r['depth_to']} m)"
            for i, r in st.session_state.soil_df.iterrows()
        ]
        selected_layer_idx = 0
        if layer_options:
            selected_layer_label = st.selectbox("Ambil Parameter Tanah dari Lapisan:", layer_options, index=0)
            selected_layer_idx = layer_options.index(selected_layer_label)
            matched_row = st.session_state.soil_df.iloc[selected_layer_idx]
            def_c = float(matched_row.get("cohesion", 20.0))
            def_phi = float(matched_row.get("friction_angle", 25.0))
            def_gamma = float(matched_row.get("gamma", 18.0))
        else:
            def_c, def_phi, def_gamma = 20.0, 25.0, 18.0

        col_s1, col_s2, col_s3 = st.columns(3)
        c_val = col_s1.number_input("c (kPa)", min_value=0.0, value=def_c, step=1.0)
        phi_val = col_s2.number_input("φ (°)", min_value=0.0, max_value=45.0, value=def_phi, step=1.0)
        gamma_val = col_s3.number_input("γ (kN/m³)", min_value=12.0, max_value=24.0, value=def_gamma, step=0.5)

    # Perform calculation
    shallow_res = calculate_shallow_foundation(
        footing_type={"Persegi": "square", "Persegi Panjang": "rectangular", "Menerus": "strip", "Lingkaran": "circular"}[footing_shape],
        width_b=width_b,
        length_l=length_l,
        depth_df=depth_df,
        cohesion_c=c_val,
        phi_deg=phi_val,
        unit_weight_gamma=gamma_val,
        gwl_depth=gwl_input,
        safety_factor=sf_req,
        applied_load_p=applied_load_p,
        method=shallow_method.lower(),
    )

    st.divider()
    st.markdown("#### 📊 Hasil Perhitungan dan Pemeriksaan Keamanan")

    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    m_col1.metric("Daya Dukung Ultimit (q_ult)", f"{shallow_res['q_ult_kpa']} kPa")
    m_col2.metric(f"Daya Dukung Izin (q_all, FK={sf_req})", f"{shallow_res['q_all_kpa']} kPa")
    m_col3.metric("Tekanan yang Bekerja (q_terapan)", f"{shallow_res['q_applied_kpa']} kPa")
    
    # Status Badge
    is_safe = shallow_res["is_safe"]
    status_html = (
        f'<div class="status-pass">✅ AMAN (FK = {shallow_res["actual_sf"]:.2f} ≥ {sf_req})</div>'
        if is_safe else
        f'<div class="status-fail">❌ TIDAK AMAN (FK = {shallow_res["actual_sf"]:.2f} &lt; {sf_req})</div>'
    )
    m_col4.markdown(f"**Status Keamanan**<br>{status_html}", unsafe_allow_html=True)

    with st.expander("🔍 Variabel Antara dan Rincian Faktor"):
        b_factors = shallow_res["factors"]
        s_factors = shallow_res["shape_factors"]
        d_factors = shallow_res["depth_factors"]
        terms = shallow_res["bearing_components"]

        gwl_case = shallow_res["gwl_case"]
        if gwl_case.startswith("Case 1:"):
            gwl_case = "Kasus 1: MAT berada pada atau di atas dasar fondasi (dw ≤ Df)"
        elif gwl_case.startswith("Case 2:"):
            gwl_case = "Kasus 2: MAT berada dalam jarak B di bawah dasar fondasi (Df < dw < Df + B)"
        else:
            gwl_case = "Kasus 3: MAT berada di bawah zona pengaruh fondasi (dw ≥ Df + B)"
        st.markdown(f"**Pengaruh Muka Air Tanah:** `{gwl_case}`")
        st.markdown(f"- Tegangan overburden efektif di dasar fondasi $q' = {shallow_res['effective_surcharge_q']:.2f}$ kPa")
        st.markdown(f"- Berat isi efektif di bawah fondasi $\\gamma' = {shallow_res['effective_gamma']:.2f}$ kN/m³")

        st.markdown("##### Faktor Tanpa Dimensi:")
        col_f1, col_f2, col_f3 = st.columns(3)
        col_f1.write(f"**Faktor Daya Dukung:**\n- $N_c = {b_factors['Nc']}$\n- $N_q = {b_factors['Nq']}$\n- $N_\\gamma = {b_factors['Ngamma']}$")
        col_f2.write(f"**Faktor Bentuk:**\n- $s_c = {s_factors['sc']}$\n- $s_q = {s_factors['sq']}$\n- $s_\\gamma = {s_factors['sgamma']}$")
        col_f3.write(f"**Faktor Kedalaman:**\n- $d_c = {d_factors['dc']}$\n- $d_q = {d_factors['dq']}$\n- $d_\\gamma = {d_factors['dgamma']}$")

        st.markdown("##### Rincian Tiga Komponen Daya Dukung:")
        col_t1, col_t2, col_t3 = st.columns(3)
        col_t1.info(f"**Komponen Kohesi ($q_c$):** {terms['cohesion_term_qc']} kPa")
        col_t2.info(f"**Komponen Overburden ($q_q$):** {terms['surcharge_term_qq']} kPa")
        col_t3.info(f"**Komponen Berat Isi ($q_\\gamma$):** {terms['unit_weight_term_qgamma']} kPa")


# =============================================================================
# TAB 4: Deep Foundation (Pondasi Tiang)
# =============================================================================
with tab_deep:
    st.subheader("Daya Dukung Aksial Fondasi Tiang")
    st.markdown("Menghitung daya dukung tiang tunggal dan efisiensi kelompok dengan metode Meyerhof (SPT) atau Luciano Decourt (1996).")

    p_col1, p_col2 = st.columns([1, 1])

    with p_col1:
        st.markdown("##### 🔩 Parameter Tiang Tunggal")
        pile_construct = st.selectbox("Jenis Pelaksanaan Tiang", ["Tiang Pancang", "Tiang Bor"])
        pile_type_arg = "driven" if pile_construct == "Tiang Pancang" else "bored"
        pile_diam = st.number_input("Diameter Tiang D (m)", min_value=0.2, max_value=2.5, value=0.5, step=0.1)
        max_soil_z = float(st.session_state.soil_df["depth_to"].max()) if not st.session_state.soil_df.empty else 20.0
        pile_depth = st.slider("Panjang Penanaman Tiang L (m)", min_value=2.0, max_value=max_soil_z, value=min(14.0, max_soil_z), step=0.5)

    with p_col2:
        st.markdown("##### ⚙️ Metode dan Faktor Keamanan")
        deep_method = st.selectbox("Metode Perhitungan", ["Meyerhof (1976)", "Luciano Decourt (1996)"])
        method_arg = "decourt" if "Decourt" in deep_method else "meyerhof"

        sf_c1, sf_c2 = st.columns(2)
        sf_end = sf_c1.number_input("FK Daya Dukung Ujung (FK_u)", min_value=2.0, max_value=4.0, value=3.0, step=0.25)
        sf_shaft = sf_c2.number_input("FK Gesekan Selimut (FK_s)", min_value=1.5, max_value=3.0, value=2.0, step=0.25)

    # Calculate Single Pile Capacity
    pile_res = calculate_single_pile_capacity(
        df_soil=st.session_state.soil_df,
        pile_type=pile_type_arg,
        diameter=pile_diam,
        pile_length=pile_depth,
        method=method_arg,
        safety_factor_end=sf_end,
        safety_factor_shaft=sf_shaft,
    )

    st.divider()
    st.markdown("#### 🎯 Hasil Daya Dukung Aksial Tiang Tunggal")

    res_c1, res_c2, res_c3, res_c4 = st.columns(4)
    res_c1.metric("Daya Dukung Ujung (Q_ujung)", f"{pile_res['q_end_bearing_kn']} kN")
    res_c2.metric("Gesekan Selimut (Q_selimut)", f"{pile_res['q_shaft_friction_kn']} kN")
    res_c3.metric("Daya Dukung Ultimit (Q_ult)", f"{pile_res['q_ult_kn']} kN")
    res_c4.metric("Daya Dukung Izin (Q_izin)", f"{pile_res['q_all_dual_sf_kn']} kN")

    # Interactive Capacity vs Depth Curve
    st.markdown("##### 📈 Kurva Daya Dukung terhadap Kedalaman Penanaman")
    df_curve = calculate_pile_capacity_depth_profile(
        df_soil=st.session_state.soil_df,
        pile_type=pile_type_arg,
        diameter=pile_diam,
        min_depth=3.0,
        max_depth=max_soil_z,
        step=1.0,
        method=method_arg,
    )

    import plotly.graph_objects as go
    fig_depth = go.Figure()
    fig_depth.add_trace(go.Scatter(x=df_curve["q_ult_kn"], y=df_curve["depth_m"], mode="lines+markers", name="Daya dukung ultimit (Q_ult)", line=dict(color="#C62828", width=2)))
    fig_depth.add_trace(go.Scatter(x=df_curve["q_all_kn"], y=df_curve["depth_m"], mode="lines+markers", name="Q_izin (kN)", line=dict(color="#1565C0", width=2)))
    fig_depth.add_hline(y=pile_depth, line_dash="dash", line_color="#2E7D32", annotation_text=f"Panjang terpilih = {pile_depth} m")
    fig_depth.update_yaxes(autorange="reversed", title_text="Kedalaman (m)")
    fig_depth.update_xaxes(title_text="Daya Dukung Tekan Aksial (kN)")
    fig_depth.update_layout(height=420, margin=dict(l=40, r=40, t=30, b=40), legend=dict(x=0.75, y=0.05))
    st.plotly_chart(fig_depth, width="stretch")

    # Pile Group Efficiency
    st.divider()
    st.markdown("#### 👥 Efisiensi dan Daya Dukung Kelompok Tiang (Rumus Converse-Labarre)")
    
    g_col1, g_col2, g_col3 = st.columns(3)
    num_rows = g_col1.number_input("Jumlah Baris (m)", min_value=1, max_value=10, value=2, step=1)
    num_cols = g_col2.number_input("Jumlah Kolom (n)", min_value=1, max_value=10, value=2, step=1)
    pile_spacing = g_col3.number_input("Jarak Antartiang s (m)", min_value=pile_diam * 2.0, max_value=5.0, value=pile_diam * 3.0, step=0.25)

    group_res = calculate_pile_group(
        n_rows=num_rows,
        n_cols=num_cols,
        spacing=pile_spacing,
        diameter=pile_diam,
        single_q_ult=pile_res["q_ult_kn"],
        single_q_all=pile_res["q_all_dual_sf_kn"],
    )

    gc_1, gc_2, gc_3, gc_4 = st.columns(4)
    gc_1.metric("Jumlah Tiang", group_res["total_piles"])
    gc_2.metric("Efisiensi (η)", f"{group_res['efficiency'] * 100:.1f} %")
    gc_3.metric("Daya Dukung Ultimit Kelompok", f"{group_res['group_q_ult_kn']:,.0f} kN")
    gc_4.metric("Daya Dukung Izin Kelompok", f"{group_res['group_q_all_kn']:,.0f} kN")


# =============================================================================
# TAB 5: ChatCopilot (GeoCopilot Workspace)
# =============================================================================
with tab_copilot:
    render_chat_copilot(
        soil_df=st.session_state.soil_df,
        project_metadata={
            "project_name": project_name,
            "borehole_id": borehole_id,
            "investigation_location": investigation_location,
            "engineer_name": engineer_name,
            "gwl": gwl_input,
            "data_kind": st.session_state.soil_data_kind,
            "shallow_res": shallow_res,
            "pile_res": pile_res,
            "group_res": group_res,
        }
    )


# =============================================================================
# TAB 6: Report Summary & Export
# =============================================================================
with tab_export:
    st.subheader("📑 Ringkasan Laporan Geoteknik")
    st.markdown("Tinjau dan ekspor hasil perhitungan untuk dokumentasi teknis.")

    summary_data = {
        "Parameter": [
            "Nama Proyek",
            "Lokasi Penyelidikan",
            "Sumber Data Tanah",
            "ID Titik Bor",
            "Insinyur",
            "Muka Air Tanah (MAT)",
            "Bentuk dan Dimensi Fondasi Dangkal",
            "Metode Fondasi Dangkal",
            "Daya Dukung Izin Fondasi Dangkal (q_all)",
            "Tekanan Terapan Fondasi Dangkal",
            "Faktor Keamanan Fondasi Dangkal (FK)",
            "Jenis Pelaksanaan Tiang",
            "Geometri Tiang (D x L)",
            "Metode Fondasi Tiang",
            "Daya Dukung Izin Tiang Tunggal (Q_izin)",
            "Konfigurasi Kelompok Tiang",
            "Daya Dukung Izin Kelompok Tiang",
        ],
        "Value": [
            project_name,
            investigation_location or "Tidak tercantum",
            st.session_state.soil_data_kind,
            borehole_id,
            engineer_name,
            f"{gwl_input:.2f} m" if gwl_input is not None else "Tidak tercantum/ditentukan",
            f"{ {'square': 'Persegi', 'rectangular': 'Persegi Panjang', 'strip': 'Menerus', 'circular': 'Lingkaran'}[shallow_res['footing_type'].lower()] } {shallow_res['dimensions']}",
            shallow_res["method"],
            f"{shallow_res['q_all_kpa']} kPa",
            f"{shallow_res['q_applied_kpa']} kPa",
            f"{shallow_res['actual_sf']:.2f} (FK rencana = {sf_req})",
            "Tiang Pancang" if pile_type_arg == "driven" else "Tiang Bor",
            f"D = {pile_res['pile_diameter_m']} m, L = {pile_res['pile_length_m']} m",
            pile_res["method"],
            f"{pile_res['q_all_dual_sf_kn']} kN",
            f"{group_res['total_piles']} tiang ({num_rows}x{num_cols}), jarak = {pile_spacing} m (η = {group_res['efficiency']*100:.1f}%)",
            f"{group_res['group_q_all_kn']:,.0f} kN",
        ]
    }
    df_summary = pd.DataFrame(summary_data)
    st.table(df_summary)

    # Unduh ringkasan sebagai CSV
    csv_buf = io.StringIO()
    df_summary.to_csv(csv_buf, index=False)
    st.download_button(
        label="📥 Unduh Ringkasan Perhitungan (CSV)",
        data=csv_buf.getvalue(),
        file_name=f"GeoFoundation_Laporan_{borehole_id}.csv",
        mime="text/csv",
    )
