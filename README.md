# 🌦️ Weather Data Pipeline — Apache Airflow + Docker

A complete, end-to-end data pipeline that automates weather data collection, processing, storage, and visualization using Apache Airflow and Docker.

---

## 📌 Project Overview

This project demonstrates a fully automated data pipeline built with Apache Airflow. It extracts real-time weather data from the Open-Meteo API, processes it, and stores it in a SQLite database. The pipeline is scheduled, monitored, and managed using Airflow, while Docker ensures a consistent and reproducible environment.

---

## 🎯 Objectives

* Build an end-to-end data pipeline using Apache Airflow
* Automate data extraction, transformation, and storage
* Implement scheduling and workflow monitoring
* Use Docker for containerized deployment
* Visualize data using Python tools

---

## ⚙️ Technologies Used

* **Apache Airflow** – Workflow orchestration
* **Python** – Data processing
* **Docker & Docker Compose** – Containerization
* **SQLite** – Data storage
* **Open-Meteo API** – Weather data source
* **Pandas & Matplotlib** – Data visualization

---

## 📁 Project Structure

```
airflow-pipeline/
├── docker-compose.yaml
├── dags/
│   └── weather_dag.py
├── scripts/
│   └── extract_weather.py
├── database/
│   └── weather.db
├── notebook/
│   └── visualization.ipynb
├── images/
│   ├── airflow-ui.png
│   ├── dag-graph.png
│   ├── pipeline.png
│   ├── task1.png
│   ├── task2.png
│   ├── docker.png
│   ├── extract.png
│   └── db.png
├── logs/
├── plugins/
├── requirements.txt
├── README.md
└── .gitignore
```

---

## 🚀 Setup Instructions

### 1️⃣ Clone or Download Project

```bash
cd airflow-pipeline
```

---

### 2️⃣ Create Required Folders & Environment File

**Windows (PowerShell):**

```bash
mkdir logs, plugins -Force
echo "AIRFLOW_UID=50000" > .env
```

**Mac/Linux:**

```bash
mkdir -p logs plugins
echo "AIRFLOW_UID=$(id -u)" > .env
```

---

### 3️⃣ Start Docker Containers

```bash
docker compose up -d
```

---

### 4️⃣ Open Airflow UI

```
http://localhost:8080
```

**Login:**

* Username: `admin`
* Password: `admin`

---

## ▶️ Running the Pipeline

### 🔹 Manual Trigger

* Open Airflow UI
* Enable DAG: `weather_data_pipeline`
* Click **Trigger DAG**
* View execution in Graph View

---

### 🔹 Automatic Schedule

Runs daily at **07:00 UTC**

---

### 🔹 CLI Trigger

```bash
docker compose exec airflow-webserver airflow dags trigger weather_data_pipeline
```

---

## 📊 Data Visualization

### Run Jupyter Notebook

```bash
pip install pandas matplotlib jupyter
cd notebook
jupyter notebook
```

Open:

```
visualization.ipynb
```

---

## 🔄 Pipeline Workflow

```
Airflow Scheduler → DAG → Python Script → Open-Meteo API → SQLite DB → Visualization
```

---

## 🗄️ Database Schema

```sql
CREATE TABLE weather_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    city TEXT NOT NULL,
    temperature REAL,
    humidity INTEGER,
    wind_speed REAL,
    weather_code INTEGER,
    feels_like REAL,
    extracted_at TEXT NOT NULL
);
```

---

## 🖼️ Project Screenshots

### 🔹 Airflow UI Dashboard

![Airflow UI](images/airflow-ui.png)

---

### 🔹 DAG Graph View

![DAG Graph](images/dag-graph.png)

---

### 🔹 Pipeline Workflow

![Pipeline](images/pipeline.png)

---

### 🔹 Task Execution (Step 1)

![Task1](images/task1.png)

---

### 🔹 Task Execution (Step 2)

![Task2](images/task2.png)

---

### 🔹 Weather Extraction Script

![Extract Script](images/extract.png)

---

### 🔹 Docker Setup

![Docker](images/docker.png)

---

### 🔹 Database View

![Database](images/db.png)

---

## 🧯 Troubleshooting

| Problem          | Solution                            |
| ---------------- | ----------------------------------- |
| Port 8080 in use | Change to `8081:8080`               |
| DAG not visible  | Wait 30s or restart scheduler       |
| DB not created   | Run DAG once                        |
| Import errors    | Restart containers                  |
| Containers fail  | Run `docker compose down --volumes` |

---

## 📈 Future Improvements

* Use PostgreSQL instead of SQLite
* Deploy pipeline to cloud (AWS/GCP)
* Add real-time dashboards
* Implement advanced data validation

---




This project is developed for academic purposes.
