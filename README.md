# 🌤️ Weather Data Pipeline — Apache Airflow + Docker

A complete, local data pipeline that:
1. **Deploys** Apache Airflow using Docker Compose
2. **Extracts** live weather data from the Open-Meteo API (free, no API key)
3. **Schedules** the extraction daily with an Airflow DAG
4. **Stores** results in a SQLite database
5. **Visualises** trends using Jupyter Notebook + pandas + matplotlib

---

## 📁 Project Structure

```
airflow-pipeline/
├── docker-compose.yaml          ← Full Airflow stack (webserver, scheduler, postgres)
├── dags/
│   └── weather_dag.py           ← Airflow DAG (runs daily at 07:00 UTC)
├── scripts/
│   └── extract_weather.py       ← Data extraction script (Open-Meteo API → SQLite)
├── database/
│   └── weather.db               ← SQLite database (auto-created on first run)
├── notebook/
│   └── visualization.ipynb      ← Jupyter charts (temperature, humidity, wind)
├── logs/                        ← Airflow task logs (auto-created)
└── plugins/                     ← Airflow plugins (empty, reserved)
```

---

## ⚙️ Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Docker Desktop | Latest | https://docs.docker.com/get-docker/ |
| Docker Compose | v2+ | Included with Docker Desktop |
| Python | 3.9+ | https://python.org (for running notebook locally) |
| Jupyter | Any | `pip install jupyter` |

---

## 🚀 Step-by-Step Setup

### Step 1 — Clone / Download the project

Place the project folder anywhere on your machine, e.g.:
```
C:\Users\YourName\airflow-pipeline\    (Windows)
~/airflow-pipeline/                    (Mac / Linux)
```

### Step 2 — Open a terminal in the project folder

```bash
cd airflow-pipeline
```

### Step 3 — Create required folders & set Airflow UID

**Windows (PowerShell):**
```powershell
mkdir logs, plugins -Force
echo "AIRFLOW_UID=50000" > .env
```

**Mac / Linux:**
```bash
mkdir -p logs plugins
echo "AIRFLOW_UID=$(id -u)" > .env
```

### Step 4 — Start the Docker containers

```bash
docker compose up -d
```

This downloads ~800 MB of images on first run. Wait ~2 minutes for all services to be healthy.

Check container status:
```bash
docker compose ps
```

Expected output — all services should show **running** or **healthy**:
```
NAME                         STATUS
airflow-pipeline-postgres-1               healthy
airflow-pipeline-airflow-webserver-1      healthy
airflow-pipeline-airflow-scheduler-1      running
```

### Step 5 — Open the Airflow Web UI

Open your browser and go to:
```
http://localhost:8080
```

Login credentials:
```
Username: admin
Password: admin
```

---

## ▶️ Running the Pipeline

### Option A — Trigger the DAG manually (recommended for testing)

1. In the Airflow UI, click **DAGs** in the top menu
2. Find **`weather_data_pipeline`** in the list
3. Toggle the DAG **ON** (blue switch on the left)
4. Click the ▶ **Trigger DAG** button (play icon under Actions)
5. Click the DAG name → **Graph** view to watch tasks execute

### Option B — Wait for automatic schedule

The DAG runs automatically every day at **07:00 UTC**.

### Option C — Trigger via CLI

```bash
docker compose exec airflow-webserver airflow dags trigger weather_data_pipeline
```

---

## 📊 Viewing Stored Data

### Option A — SQL query inside Docker

```bash
docker compose exec airflow-webserver \
  python -c "
import sqlite3, os
conn = sqlite3.connect('/opt/airflow/database/weather.db')
cur  = conn.cursor()
cur.execute('SELECT * FROM weather_data ORDER BY extracted_at DESC LIMIT 20')
for row in cur.fetchall(): print(row)
conn.close()
"
```

### Option B — DB Browser for SQLite (GUI)

1. Download from https://sqlitebrowser.org/
2. Open `database/weather.db` directly from your project folder

---

## 📈 Running the Visualization

### Step 1 — Install Python dependencies locally

```bash
pip install pandas matplotlib jupyter
```

### Step 2 — Launch Jupyter

```bash
cd notebook
jupyter notebook
```

### Step 3 — Open and run the notebook

1. Click `visualization.ipynb`
2. Run each cell with **Shift + Enter** (or click ▶ Run All)
3. Charts are also saved as `.png` files in the `database/` folder

---

## 🛑 Stopping the Pipeline

```bash
# Stop containers (data is preserved)
docker compose down

# Stop AND delete all data (including the postgres DB)
docker compose down --volumes
```

---

## 🔄 How the Pipeline Works

```
┌──────────────┐     every day      ┌─────────────────────┐
│  Airflow     │  ─────07:00 UTC──► │  weather_dag.py     │
│  Scheduler   │                    │  (DAG orchestrator) │
└──────────────┘                    └──────────┬──────────┘
                                               │ PythonOperator
                                               ▼
                                    ┌─────────────────────┐
                                    │ extract_weather.py  │
                                    │                     │
                                    │  Open-Meteo API     │
                                    │  → London           │
                                    │  → New York         │
                                    │  → Tokyo            │
                                    └──────────┬──────────┘
                                               │ INSERT
                                               ▼
                                    ┌─────────────────────┐
                                    │  weather.db         │
                                    │  (SQLite)           │
                                    └──────────┬──────────┘
                                               │ SELECT
                                               ▼
                                    ┌─────────────────────┐
                                    │ visualization.ipynb │
                                    │  pandas + matplotlib│
                                    └─────────────────────┘
```

### Data Flow Details

| Step | What Happens |
|------|-------------|
| 1. Scheduler triggers DAG | Airflow scheduler checks cron `0 7 * * *` and triggers a DAG run |
| 2. `extract_weather` task runs | `PythonOperator` calls `run_extraction()` in `extract_weather.py` |
| 3. API call | HTTP GET to `https://api.open-meteo.com/v1/forecast` for each city |
| 4. Data parsing | JSON response → Python dict with 5 attributes + UTC timestamp |
| 5. Database insert | `INSERT INTO weather_data ...` in `/opt/airflow/database/weather.db` |
| 6. `log_summary` task runs | Reads XCom result and logs success/failure counts |
| 7. Visualization | Jupyter notebook queries SQLite → pandas DataFrame → matplotlib charts |

---

## 🗄️ Database Schema

```sql
CREATE TABLE weather_data (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    city          TEXT    NOT NULL,       -- e.g. "London"
    temperature   REAL,                   -- air temp at 2m, °C
    humidity      INTEGER,               -- relative humidity, %
    wind_speed    REAL,                   -- wind speed at 10m, km/h
    weather_code  INTEGER,               -- WMO weather code (0 = clear sky)
    feels_like    REAL,                   -- apparent temperature, °C
    extracted_at  TEXT    NOT NULL        -- UTC ISO-8601 timestamp
);
```

---

## 🧯 Troubleshooting

| Problem | Fix |
|---------|-----|
| Port 8080 already in use | Change `"8080:8080"` to `"8081:8080"` in `docker-compose.yaml` |
| DAG not visible in UI | Wait 30 s — scheduler scans every 30 s. Check `docker compose logs airflow-scheduler` |
| `weather.db` not created | Run the DAG once. The script creates it automatically |
| Import error in task logs | Run `docker compose restart airflow-scheduler` |
| Containers not starting | Run `docker compose down --volumes` then `docker compose up -d` again |

---

## 📝 API Reference

This project uses [Open-Meteo](https://open-meteo.com/):
- ✅ Free, no API key required
- ✅ No rate limits for personal use
- ✅ Covers worldwide coordinates
- Docs: https://open-meteo.com/en/docs
