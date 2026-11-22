from __future__ import annotations
import io
from typing import Any
import pandas as pd
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from modules.pdf_reader import get_sample_soil_data, get_empty_soil_data, parse_soil_investigation_pdf, standardize_borehole_table
from modules.foundation_calculation import calculate_shallow_foundation, calculate_single_pile_capacity, calculate_pile_capacity_depth_profile, calculate_pile_group
from modules.chat_copilot import generate_geotechnical_response

app = FastAPI(title="GeoFoundation API", version="1.0.0", description="Python calculation engine for GeoFoundation")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

class SoilLayer(BaseModel):
    depth_from: float = Field(ge=0)
    depth_to: float = Field(gt=0)
    soil_type: str = "Tanah"
    description: str = ""
    n_spt: float | None = None
    qc: float | None = None
    qc_unit: str | None = None
    gamma: float | None = None
    cohesion: float | None = None
    friction_angle: float | None = None
    water_content_pct: float | None = None
    liquid_limit_pct: float | None = None
    plastic_limit_pct: float | None = None
    specific_gravity: float | None = None
    void_ratio: float | None = None
    unconfined_compressive_strength_kpa: float | None = None

class SoilPayload(BaseModel):
    layers: list[SoilLayer]

class ShallowPayload(BaseModel):
    footing_type: str = "square"
    width_b: float = Field(gt=0)
    length_l: float = Field(gt=0)
    depth_df: float = Field(ge=0)
    cohesion_c: float = Field(ge=0)
    phi_deg: float = Field(ge=0, le=50)
    unit_weight_gamma: float = Field(gt=0)
    gwl_depth: float | None = None
    gamma_sat: float = 19.0
    gamma_water: float = 9.81
    applied_load_p: float = 0.0
    safety_factor: float = 3.0
    method: str = "meyerhof"

class PilePayload(BaseModel):
    layers: list[SoilLayer]
    pile_type: str = "driven"
    diameter: float = Field(gt=0)
    pile_length: float = Field(gt=0)
    method: str = "meyerhof"
    safety_factor_end: float = 3.0
    safety_factor_shaft: float = 2.0
    safety_factor_total: float = 2.5

class GroupPayload(BaseModel):
    n_rows: int = Field(ge=1)
    n_cols: int = Field(ge=1)
    spacing: float = Field(gt=0)
    diameter: float = Field(gt=0)
    single_q_ult: float = Field(ge=0)
    single_q_all: float = Field(ge=0)

class ChatPayload(BaseModel):
    query: str
    layers: list[SoilLayer] = []
    project_name: str = "Proyek Geoteknik"
    borehole_id: str = "BH-01"
    gwl: float | None = None
    data_kind: str = "Data aktif"

@app.get("/api/health")
def health():
    return {"status": "ok", "service": "GeoFoundation API", "version": "1.0.0"}

@app.get("/api/sample-soil")
def sample_soil():
    return {"layers": get_sample_soil_data().where(pd.notna(get_sample_soil_data()), None).to_dict(orient="records"), "source": "sample", "notice": "Data demonstrasi BH-01, bukan data investigasi aktual."}

@app.post("/api/shallow-foundation")
def shallow(payload: ShallowPayload):
    try:
        return calculate_shallow_foundation(**payload.model_dump())
    except Exception as e:
        raise HTTPException(422, str(e))

@app.post("/api/pile-capacity")
def pile(payload: PilePayload):
    try:
        df = pd.DataFrame([x.model_dump() for x in payload.layers])
        if df.empty: raise ValueError("Data lapisan tanah belum tersedia.")
        args = payload.model_dump(exclude={"layers"})
        return calculate_single_pile_capacity(df_soil=df, **args)
    except Exception as e:
        raise HTTPException(422, str(e))

@app.post("/api/pile-profile")
def pile_profile(payload: PilePayload):
    try:
        df = pd.DataFrame([x.model_dump() for x in payload.layers])
        if df.empty: raise ValueError("Data lapisan tanah belum tersedia.")
        return calculate_pile_capacity_depth_profile(df, pile_type=payload.pile_type, diameter=payload.diameter, max_depth=payload.pile_length, method=payload.method).to_dict(orient="records")
    except Exception as e:
        raise HTTPException(422, str(e))

@app.post("/api/pile-group")
def pile_group(payload: GroupPayload):
    try: return calculate_pile_group(**payload.model_dump())
    except Exception as e: raise HTTPException(422, str(e))

@app.post("/api/soil/standardize")
def standardize(payload: SoilPayload):
    df = pd.DataFrame([x.model_dump() for x in payload.layers])
    if df.empty: raise HTTPException(422, "Tidak ada data lapisan.")
    return {"layers": df.where(pd.notna(df), None).to_dict(orient="records")}

@app.post("/api/pdf/parse")
async def parse_pdf(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Unggah berkas PDF.")
    raw = await file.read()
    if len(raw) > 25 * 1024 * 1024: raise HTTPException(413, "Ukuran PDF maksimum 25 MB.")
    try:
        df, metadata = parse_soil_investigation_pdf(io.BytesIO(raw))
        return {"layers": df.where(pd.notna(df), None).to_dict(orient="records"), "metadata": metadata, "needs_review": True, "notice": "Hasil ekstraksi harus diperiksa dan dikonfirmasi sebelum dipakai untuk analisis. OCR tidak dijalankan oleh parser ini."}
    except Exception as e:
        raise HTTPException(422, f"PDF tidak dapat diproses: {e}")

@app.post("/api/geocopilot")
def copilot(payload: ChatPayload):
    try:
        df = pd.DataFrame([x.model_dump() for x in payload.layers])
        if df.empty: df = get_empty_soil_data()
        metadata: dict[str, Any] = {"project_name": payload.project_name, "borehole_id": payload.borehole_id, "gwl": payload.gwl, "data_kind": payload.data_kind}
        return {"response": generate_geotechnical_response(payload.query, df, metadata)}
    except Exception as e:
        raise HTTPException(422, str(e))
