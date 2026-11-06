# 🏗️ GeoFoundation

**GeoFoundation** is an interactive geotechnical engineering application designed for civil engineering students and practitioners (APLIKOM - Aplikasi Komputer Teknik Sipil). It integrates soil borehole log parsing, stratigraphy and N-SPT depth visualization, and shallow & deep foundation bearing capacity calculations.

---

## 📁 Project Architecture

```
GeoFoundation/
├── app.py                      # Main Streamlit web application
├── requirements.txt            # Python dependencies
├── README.md                   # Project documentation & geotechnical reference
├── .gitignore                  # Git ignore rules
├── data/                       # Soil investigation reports, borehole logs, PDFs
│   └── .gitkeep
├── modules/
│   ├── chat_copilot.py         # GeoCopilot geotechnical engineering assistant workspace
│   ├── pdf_reader.py           # Soil investigation & borehole PDF/table parser
│   ├── soil_visualization.py   # Stratigraphy column & N-SPT profile visualizer
│   └── foundation_calculation.py# Shallow & deep foundation calculation engine
└── tests/
    ├── test_calculation.py     # Unit test suite for geotechnical formulas
    ├── test_chat_copilot.py    # Unit test suite for GeoCopilot assistant
    └── test_pdf_reader.py      # Unit test suite for PDF parser
```

---

## 🚀 Key Features

1. **Borehole Log & PDF Ingestion**:
   - Parse soil investigation PDF reports and tabular logs (depth intervals, soil descriptions, N-SPT values).
   - Built-in realistic sample borehole (`BH-01`) for instant testing and demonstration.
   - Interactive data table editor to customize soil layer parameters ($z$, $c$, $\phi$, $\gamma$).

2. **Stratigraphy & N-SPT Visualization**:
   - Dual-panel interactive chart: Geotechnical soil stratigraphy column paired with the N-SPT penetration resistance curve.
   - Distinct geotechnical color coding for clay, silt, sand, gravel, and rock strata.
   - Ground Water Level (GWL / Muka Air Tanah - MAT) marker.
   - Export publication-ready high-resolution plots via Matplotlib or interactive Plotly graphs.

3. **Shallow Foundation Analysis (Pondasi Dangkal)**:
   - **Formulations**: Meyerhof (1963) and Terzaghi (1943) bearing capacity equations.
   - **Footing Shapes**: Strip / Continuous, Square, Rectangular, and Circular.
   - **Groundwater Effects**: Automatic calculation of effective surcharge ($q'$) and effective unit weight ($\gamma'$) based on the water table position relative to embedment depth ($D_f$) and footing width ($B$).
   - **Safety Assessment**: Evaluates ultimate bearing capacity ($q_{ult}$), allowable capacity ($q_{all}$), applied contact pressure ($q_{applied}$), and factor of safety ($FS$).

4. **Deep Foundation Analysis (Pondasi Tiang)**:
   - **Methods**: Meyerhof (1976) SPT method & Luciano Decourt (1996) method.
   - **Pile Types**: Driven piles (tiang pancang) and bored piles (tiang bor).
   - **Layer-by-Layer Integration**: Evaluates unit skin friction ($f_s$) and end bearing ($q_b$) along the embedded pile length.
   - **Capacity vs. Depth Curve**: Generates continuous axial compression capacity curves across various depths.
   - **Pile Group Analysis**: Calculates group efficiency ($\eta$) using the Converse-Labarre formula for $m \times n$ pile configurations.

5. **GeoCopilot Geotechnical Workspace (ChatCopilot)**:
   - Interactive engineering consulting assistant designed for geotechnical professionals.
   - Professional visual identity with navy blue palette, earth-tone stratigraphy accents, and minimal borehole core branding.
   - Quick access consultation cards: Stratigraphy analysis, SPT/CPT evaluation, foundation capacity methodology, and standards/codes (SNI 8460:2017).
   - Fully integrated with active borehole investigation data and computed foundation results.

6. **Reporting & Data Export**:
   - Comprehensive technical summary table for engineering calculation sheets.
   - One-click export of calculation results to CSV format.

---

## 📐 Geotechnical Engineering Formulations

### 1. Shallow Foundation Bearing Capacity

$$q_{ult} = c \cdot N_c \cdot s_c \cdot d_c + q' \cdot N_q \cdot s_q \cdot d_q + \frac{1}{2} \cdot \gamma' \cdot B \cdot N_\gamma \cdot s_\gamma \cdot d_\gamma$$

- **Meyerhof Bearing Capacity Factors**:
  $$N_q = e^{\pi \tan\phi} \tan^2\left(45^\circ + \frac{\phi}{2}\right)$$
  $$N_c = (N_q - 1)\cot\phi \quad (\text{for } \phi = 0^\circ, N_c = 5.14)$$
  $$N_\gamma = (N_q - 1)\tan(1.4\phi)$$

- **Allowable Bearing Capacity**:
  $$q_{all} = \frac{q_{ult}}{FS} \quad (FS \ge 3.0)$$

### 2. Deep Foundation Bearing Capacity (Single Pile)

$$Q_{ult} = Q_b + Q_s = q_b \cdot A_b + \sum (f_{si} \cdot A_{si})$$

- **Meyerhof (1976) SPT Method**:
  - Base Resistance: $q_b = 40 \cdot N_{SPT} \cdot \left(\frac{L}{D}\right) \le 400 \cdot N_{SPT} \text{ (kPa)}$
  - Shaft Friction (Sand): $f_s = 2.0 \cdot N_{SPT} \text{ (kPa)}$
  - Shaft Friction (Clay): $f_s = \alpha \cdot c_u \approx 3.125 \cdot N_{SPT} \text{ (kPa)}$

- **Luciano Decourt (1996) Method**:
  $$Q_{ult} = K_b \cdot \overline{N_b} \cdot A_b + \alpha \cdot \left(\frac{\overline{N_s}}{3} + 1\right) \cdot A_s$$

### 3. Pile Group Efficiency (Converse-Labarre)

$$\eta = 1 - \theta \cdot \frac{(n-1)m + (m-1)n}{90 \cdot m \cdot n}$$

where $\theta = \arctan(D/s)$ in degrees, $m$ is the number of rows, $n$ is the number of columns, and $s$ is center-to-center pile spacing.

---

## 🛠️ Installation & Setup

1. **Clone or Navigate to the Repository**:
   ```bash
   cd GeoFoundation
   ```

2. **Create and Activate a Virtual Environment** (recommended):
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # macOS/Linux:
   source .venv/bin/activate
   ```

3. **Install Requirements**:
   ```bash
   pip install -r requirements.txt
   ```

---

## 🖥️ Running the Application

Launch the Streamlit web dashboard:
```bash
streamlit run app.py
```

Once started, open `http://localhost:8501` in your browser.

---

## 🧪 Running Unit Tests

Run the test suite using `pytest`:
```bash
pytest tests/ -v
```

---

## 📄 License
This project is developed for educational and academic purposes under the Civil Engineering Department (APLIKOM).
