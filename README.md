# GeoFoundation Web — React + FastAPI

Migrasi awal GeoFoundation dari Streamlit ke frontend React dan backend Python FastAPI.

## Arsitektur
- `frontend/`: React + TypeScript + Vite + Recharts + Lucide; deploy ke Netlify.
- `backend/`: FastAPI; deploy sebagai layanan Python (contoh konfigurasi Render tersedia di `backend/render.yaml`).
- Modul perhitungan, parser PDF, dan generator respons GeoCopilot berasal dari proyek sumber.

## Menjalankan lokal

Terminal 1 — backend:
```bash
cd backend
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```
API docs: http://localhost:8000/docs

Terminal 2 — frontend:
```bash
cd frontend
npm install
copy .env.example .env   # Windows PowerShell: Copy-Item .env.example .env
npm run dev
```
Buka http://localhost:5173.

## Deploy
1. Push folder proyek ini ke repository GitHub baru.
2. Deploy backend sebagai Python web service dengan root directory `backend`, build `pip install -r requirements.txt`, start `uvicorn main:app --host 0.0.0.0 --port $PORT`.
3. Deploy frontend di Netlify dengan base directory `frontend`, build command `npm run build`, publish directory `dist`.
4. Tambahkan environment variable Netlify `VITE_API_URL` berisi URL publik backend + `/` (contoh `https://nama-api.onrender.com`). Setelah mengubah env var, trigger redeploy.
5. Untuk produksi, batasi CORS di `backend/main.py` ke domain Netlify yang benar.

## Catatan cakupan versi alpha
- Sudah tersedia: dashboard, pengelolaan metadata proyek dalam sesi browser, tabel edit lapisan tanah, visualisasi stratigrafi dan N-SPT, impor PDF melalui parser lama (ekstraksi tanpa OCR; hasil wajib diverifikasi), analisis fondasi dangkal, analisis tiang tunggal, efisiensi kelompok tiang, dan endpoint GeoCopilot rule-based.
- Belum dipindahkan/diimplementasikan: autentikasi, database/persistensi proyek, impor Excel/CSV UI, ekspor laporan PDF, visualisasi kapasitas tiang terhadap kedalaman, dan pengelolaan proyek multi-user. Hal-hal ini harus dikerjakan dan diuji pada iterasi berikutnya.
- Jangan gunakan data demonstrasi sebagai data desain aktual. Hasil perhitungan perlu ditinjau insinyur geoteknik dan dibandingkan dengan standar/desain proyek.
- Kode rumus perhitungan disalin apa adanya dari modul sumber untuk menjaga kesetaraan; migrasi UI/API bukan validasi independen atas ketepatan metode.

## Legacy Streamlit version
The untouched original Streamlit application is preserved under `legacy_streamlit/` as a rollback/reference copy. It is not used by the new React/FastAPI runtime.
