"""
soil_visualization.py
Visualization module for geotechnical borehole logs, soil stratigraphy,
and N-SPT depth profiles using Plotly and Matplotlib.
Part of the GeoFoundation geotechnical analysis suite.
"""

from typing import Dict, List, Optional
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


SOIL_COLORS = {
    "clay": "#7986CB",          # Soft Indigo / Periwinkle
    "silty clay": "#5C6BC0",
    "stiff clay": "#3F51B5",
    "hard clay": "#283593",
    "silt": "#A1887F",          # Earthy Brown-Grey
    "sand": "#FFE082",          # Warm Sand Yellow
    "dense sand": "#FFD54F",
    "gravel": "#B0BEC5",        # Slate Grey
    "rock": "#78909C",
    "peat": "#4E342E",          # Deep Organic Brown
    "lempung keras": "#283593",
    "lempung kaku": "#3F51B5",
    "lempung lanauan": "#5C6BC0",
    "lempung": "#7986CB",
    "pasir padat": "#FFD54F",
    "pasir": "#FFE082",
    "batu lanau": "#78909C",
    "default": "#CFD8DC",
}


def get_soil_color(soil_type: str) -> str:
    """Returns hexadecimal color code for a given soil description."""
    st = str(soil_type).lower()
    for key, color in SOIL_COLORS.items():
        if key in st:
            return color
    return SOIL_COLORS["default"]


def create_interactive_soil_profile(
    df: pd.DataFrame,
    gwl: Optional[float] = None,
    borehole_id: str = "BH-01"
) -> go.Figure:
    """
    Creates an interactive dual-panel Plotly figure:
    Panel 1: Soil Stratigraphy Column with labels.
    Panel 2: N-SPT Depth Curve with geotechnical consistency zones.
    """
    fig = make_subplots(
        rows=1,
        cols=2,
        column_widths=[0.35, 0.65],
        shared_yaxes=True,
        subplot_titles=("Stratigrafi Tanah", "Uji Penetrasi Standar (N-SPT)"),
        horizontal_spacing=0.08,
    )

    max_depth = float(df["depth_to"].max()) if not df.empty else 20.0

    # 1. Stratigraphy Column (Bar/Shape markers)
    for idx, row in df.iterrows():
        z_from = row["depth_from"]
        z_to = row["depth_to"]
        thick = z_to - z_from
        mid_z = (z_from + z_to) / 2.0
        stype = row.get("soil_type", "Soil")
        desc = row.get("description", stype)
        color = get_soil_color(stype)

        # Bar block for layer
        fig.add_trace(
            go.Bar(
                x=[1.0],
                y=[thick],
                base=z_from,
                name=f"{stype} ({z_from:.1f}-{z_to:.1f}m)",
                marker=dict(color=color, line=dict(color="#333333", width=1.2)),
                hovertext=(
                    f"<b>Layer {idx + 1}: {stype}</b><br>"
                    f"Kedalaman: {z_from:.1f} m sampai {z_to:.1f} m (Δz = {thick:.1f} m)<br>"
                    f"N-SPT: {row.get('n_spt', '-')}<br>"
                    f"γ: {row.get('gamma', '-')} kN/m³<br>"
                    f"c: {row.get('cohesion', '-')} kPa, φ: {row.get('friction_angle', '-')}°<br>"
                    f"Deskripsi: {desc}"
                ),
                hoverinfo="text",
                showlegend=False,
                orientation="v",
            ),
            row=1,
            col=1,
        )

        # Text label inside column
        fig.add_annotation(
            x=0.5,
            y=mid_z,
            text=f"<b>{stype}</b><br>({z_from:.1f} - {z_to:.1f}m)",
            showarrow=False,
            xref="x1",
            yref="y1",
            font=dict(size=11, color="#1A237E"),
            align="center",
        )

    # 2. N-SPT Depth Curve (Panel 2)
    spt_depths = []
    spt_values = []
    hover_texts = []

    for _, row in df.iterrows():
        mid_z = (row["depth_from"] + row["depth_to"]) / 2.0
        nspt = row["n_spt"]
        spt_depths.append(mid_z)
        spt_values.append(nspt)
        hover_texts.append(
            f"Kedalaman: {mid_z:.1f} m<br>N-SPT: {nspt}<br>Lapisan: {row.get('soil_type', '')}"
        )

    fig.add_trace(
        go.Scatter(
            x=spt_values,
            y=spt_depths,
            mode="lines+markers",
            line=dict(color="#D32F2F", width=2.5),
            marker=dict(size=8, color="#B71C1C", symbol="circle"),
            name="N-SPT",
            hovertext=hover_texts,
            hoverinfo="text",
        ),
        row=1,
        col=2,
    )

    # Add background reference bands for N-SPT consistency
    # Soft (0-10), Medium (10-30), Dense/Hard (>30)
    fig.add_vrect(x0=0, x1=10, fillcolor="#ECEFF1", opacity=0.4, layer="below", line_width=0, col=2, row=1)
    fig.add_vrect(x0=10, x1=30, fillcolor="#E0F2F1", opacity=0.4, layer="below", line_width=0, col=2, row=1)
    fig.add_vrect(x0=30, x1=60, fillcolor="#FFF3E0", opacity=0.4, layer="below", line_width=0, col=2, row=1)

    # Ground Water Level (GWL / MAT) indicator line
    if gwl is not None and gwl >= 0:
        for col_idx in [1, 2]:
            fig.add_hline(
                y=gwl,
                line_dash="dash",
                line_color="#0288D1",
                line_width=2,
                annotation_text=f"MAT: {gwl:.2f} m",
                annotation_position="bottom right" if col_idx == 2 else "top left",
                annotation_font_color="#01579B",
                row=1,
                col=col_idx,
            )

    # Axis formatting
    fig.update_yaxes(
        autorange="reversed",
        title_text="Kedalaman dari Permukaan Tanah (m)",
        range=[max_depth + 1.0, 0],
        gridcolor="#E0E0E0",
        zeroline=False,
    )
    fig.update_xaxes(
        showticklabels=False,
        showgrid=False,
        zeroline=False,
        range=[0, 1.0],
        row=1,
        col=1,
    )
    fig.update_xaxes(
        title_text="Tahanan Penetrasi Standar (N-SPT)",
        range=[0, max(60, max(spt_values, default=50) + 10)],
        gridcolor="#E0E0E0",
        zeroline=True,
        row=1,
        col=2,
    )

    fig.update_layout(
        title=dict(
            text=f"<b>Log Titik Bor dan Profil Stratigrafi Tanah — {borehole_id}</b>",
            x=0.5,
            xanchor="center",
            font=dict(size=16),
        ),
        barmode="stack",
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FAFAFA",
        height=650,
        margin=dict(l=60, r=40, t=80, b=60),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    return fig


def create_matplotlib_soil_profile(
    df: pd.DataFrame,
    gwl: Optional[float] = None,
    borehole_id: str = "BH-01"
) -> plt.Figure:
    """
    Creates a publication-ready Matplotlib figure for engineering reports.
    """
    fig, (ax_strat, ax_spt) = plt.subplots(
        1, 2, figsize=(9, 8), sharey=True, gridspec_kw={"width_ratios": [1, 2]}
    )

    max_depth = float(df["depth_to"].max()) if not df.empty else 20.0

    # Panel 1: Stratigraphy Column
    for idx, row in df.iterrows():
        z_from = row["depth_from"]
        z_to = row["depth_to"]
        thick = z_to - z_from
        mid_z = (z_from + z_to) / 2.0
        stype = row.get("soil_type", "Soil")
        color = get_soil_color(stype)

        rect = patches.Rectangle(
            (0.1, z_from), 0.8, thick, linewidth=1.2, edgecolor="#263238", facecolor=color
        )
        ax_strat.add_patch(rect)
        ax_strat.text(
            0.5,
            mid_z,
            f"{stype}\n({z_from:.1f}-{z_to:.1f}m)",
            ha="center",
            va="center",
            fontsize=9,
            fontweight="bold",
            color="#1A237E",
        )

    ax_strat.set_xlim(0, 1)
    ax_strat.set_xticks([])
    ax_strat.set_title("Stratigrafi", fontsize=11, fontweight="bold", pad=10)
    ax_strat.set_ylabel("Kedalaman (m)", fontsize=11, fontweight="bold")

    # Panel 2: N-SPT Profile
    spt_depths = [(r["depth_from"] + r["depth_to"]) / 2.0 for _, r in df.iterrows()]
    spt_vals = [r["n_spt"] for _, r in df.iterrows()]

    ax_spt.plot(spt_vals, spt_depths, "o-", color="#C62828", linewidth=2, markersize=6, label="N-SPT")
    ax_spt.set_title("Tahanan N-SPT", fontsize=11, fontweight="bold", pad=10)
    ax_spt.set_xlabel("Jumlah Pukulan N-SPT", fontsize=11, fontweight="bold")
    ax_spt.grid(True, linestyle="--", alpha=0.6)
    ax_spt.set_xlim(0, max(60, max(spt_vals, default=50) + 10))

    # Ground Water Level
    if gwl is not None and gwl >= 0:
        ax_strat.axhline(gwl, color="#0288D1", linestyle="--", linewidth=1.8)
        ax_spt.axhline(gwl, color="#0288D1", linestyle="--", linewidth=1.8, label=f"MAT (-{gwl:.2f} m)")
        ax_spt.legend(loc="upper right", fontsize=9)

    ax_strat.set_ylim(max_depth + 1.0, 0)  # Invert depth
    fig.suptitle(f"Penyelidikan Titik Bor: {borehole_id}", fontsize=14, fontweight="bold", y=0.98)
    fig.tight_layout()

    return fig
