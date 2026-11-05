# FLOOD-X — Developer Setup & Operation Guide

## 1. Prerequisites
- **Operating System**: Windows 10/11, macOS, or Ubuntu Linux 22.04+
- **Python**: Version 3.11 or 3.12
- **Node.js**: Version 20.x or 22.x LTS (with `npm` >= 10)
- **Docker**: Docker Desktop with Docker Compose v2 (optional for local mock dev, required for PostGIS)

---

## 2. Quickstart Step-by-Step

### Step 2.1 — Clone & Configure Environment
```bash
# Clone the repository
cd FLOODX

# Copy environment configuration templates
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
cp mobile/.env.example mobile/.env
```

---

### Step 2.2 — PostGIS Database (Docker)
To start the containerized PostgreSQL 16 + PostGIS 3.4 database:
```bash
docker compose up -d db
```
Verify container status:
```bash
docker compose ps
docker compose logs -f db
```

*Note: If Docker is not available on your workstation, the backend runs in **Degraded Mode** automatically and returns `status: "degraded"` on `/api/v1/health` without crashing.*

---

### Step 2.3 — Backend Setup & Execution
```bash
# 1. Navigate to backend directory
cd backend

# 2. Create virtual environment
python -m venv .venv

# 3. Activate virtual environment
# On Windows (PowerShell):
.venv\Scripts\Activate.ps1
# On Linux/macOS:
source .venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Run automated tests
pytest tests/ -v

# 6. Start development server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Endpoints available:
- **Root Discovery**: `http://localhost:8000/`
- **Interactive Swagger Docs**: `http://localhost:8000/api/v1/docs`
- **ReDoc Docs**: `http://localhost:8000/api/v1/redoc`
- **Health Verification**: `http://localhost:8000/api/v1/health`
- **System Information**: `http://localhost:8000/api/v1/system/info`

---

### Step 2.4 — Frontend Dashboard Setup & Execution
```bash
# 1. Navigate to frontend directory
cd frontend

# 2. Install npm dependencies
npm install

# 3. Run TypeScript type checks
npm run build

# 4. Start Vite development server
npm run dev
```
Dashboard available at: `http://localhost:5173`

---

### Step 2.5 — Mobile Application Setup (Expo)
```bash
# 1. Navigate to mobile directory
cd mobile

# 2. Install dependencies
npm install

# 3. Start Expo development server
npx expo start
```
- Press `a` in the terminal to launch on connected Android Emulator.
- Scan QR code with the **Expo Go** app on your physical Android device.

---

## 3. Physical Android Device API Connection Guide

When testing on a physical Android device, `localhost` refers to the Android phone itself, not your development PC.
1. Find your development PC's local WiFi IP (e.g., `ipconfig` on Windows -> IPv4 Address, e.g., `192.168.1.45`).
2. Open `mobile/.env`.
3. Set `EXPO_PUBLIC_API_BASE_URL=http://192.168.1.45:8000/api/v1`.
4. Ensure your phone and PC are connected to the same WiFi network.
5. For Android Emulator, use `http://10.0.2.2:8000/api/v1` (the default emulator gateway to host loopback).

---

## 4. Running Migrations with Alembic
```bash
cd backend
alembic upgrade head
```

