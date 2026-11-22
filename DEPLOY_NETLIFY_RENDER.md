# Panduan menjalankan dan deploy GeoFoundation Web

## Lokal di VS Code (Windows)

Buka folder `GeoFoundation_Web` di VS Code. Jalankan dua terminal.

### Terminal 1 — API Python
```powershell
cd backend
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```
Jika PowerShell memblokir aktivasi, jalankan `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` lalu aktivasi lagi. API docs tersedia di `http://localhost:8000/docs`.

### Terminal 2 — React
```powershell
cd frontend
npm install
Copy-Item .env.example .env
npm run dev
```
Buka `http://localhost:5173`.

## Deploy backend (contoh Render)
1. Push seluruh folder ini ke repository GitHub.
2. Buat Web Service baru dari repository tersebut.
3. Root Directory: `backend`.
4. Build Command: `pip install -r requirements.txt`.
5. Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`.
6. Setelah aktif, catat URL backend, misalnya `https://geofoundation-api.onrender.com`.

## Deploy frontend Netlify
1. Tambahkan repository GitHub yang sama ke Netlify.
2. Base directory: `frontend`.
3. Build command: `npm run build`.
4. Publish directory: `dist`.
5. Environment variable: `VITE_API_URL` = URL backend tanpa slash di akhir.
6. Deploy. Setelah deployment, uji API status dan fungsi impor PDF/analisis.

Untuk produksi, ubah CORS `allow_origins=["*"]` pada `backend/main.py` menjadi domain Netlify yang sebenarnya. Jangan menyimpan API key rahasia di variabel frontend `VITE_*`.
