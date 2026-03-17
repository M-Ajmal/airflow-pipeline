"""
weather_dag.py
--------------
Airflow DAG: Daily Weather Data Extraction Pipeline
 - Runs once per day at 07:00 UTC
 - Uses PythonOperator to call the extraction script
 - Logs execution details and result summary via XCom
"""

from __future__ import annotations

import sys
import os
import logging
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

# ──────────────────────────────────────────────────────────────
# Make our /scripts folder importable inside Airflow
# ──────────────────────────────────────────────────────────────
SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────
# TASK FUNCTIONS
# ──────────────────────────────────────────────────────────────

def task_extract_weather(**context):
    """
    Task 1: Extract weather data for all configured cities and
    store results in SQLite.  Pushes a summary dict to XCom so
    downstream tasks (or monitoring) can inspect it.
    """
    logger.info("Starting weather extraction task ...")
    logger.info(f"DAG run ID     : {context['run_id']}")
    logger.info(f"Execution date : {context['ds']}")

    # Import here so the import error (if any) shows up in task logs
    from extract_weather import run_extraction

    result = run_extraction()

    # Push result to XCom for downstream tasks or monitoring
    context["ti"].xcom_push(key="extraction_result", value=result)

    logger.info(f"Extraction result: {result}")
    return result


def task_log_summary(**context):
    """
    Task 2: Pull the XCom result from the extraction task and
    write a human-readable summary to the Airflow task log.
    """
    ti     = context["ti"]
    result = ti.xcom_pull(task_ids="extract_weather", key="extraction_result")

    logger.info("=" * 50)
    logger.info("  DAILY WEATHER PIPELINE — EXECUTION SUMMARY")
    logger.info("=" * 50)
    logger.info(f"  DAG run        : {context['run_id']}")
    logger.info(f"  Execution date : {context['ds']}")

    if result:
        logger.info(f"  Extracted at   : {result.get('extracted_at', 'N/A')}")
        logger.info(f"  Cities saved   : {result.get('cities_success', 0)}")
        logger.info(f"  Cities failed  : {result.get('cities_failed',  0)}")
    else:
        logger.warning("  No result received from extraction task.")

    logger.info("=" * 50)
    return "Summary logged successfully"


# ──────────────────────────────────────────────────────────────
# DEFAULT ARGUMENTS applied to every task in this DAG
# ──────────────────────────────────────────────────────────────

default_args = {
    "owner":            "student",           # visible in Airflow UI
    "depends_on_past":  False,               # each run is independent
    "email_on_failure": False,               # disable email alerts
    "email_on_retry":   False,
    "retries":          2,                   # retry twice on failure
    "retry_delay":      timedelta(minutes=5),# wait 5 min between retries
}


# ──────────────────────────────────────────────────────────────
# DAG DEFINITION
# ──────────────────────────────────────────────────────────────

with DAG(
    dag_id="weather_data_pipeline",           # unique name shown in UI
    description="Daily extraction of weather data from Open-Meteo API",
    default_args=default_args,
    schedule_interval="0 7 * * *",            # run every day at 07:00 UTC
    start_date=datetime(2024, 1, 1),          # backfill start (won't run if catchup=False)
    catchup=False,                            # don't run for past dates
    tags=["weather", "data-pipeline", "coursework"],
) as dag:

    # ── Task 1: Extract & store weather data ──────────────────
    extract_weather = PythonOperator(
        task_id="extract_weather",
        python_callable=task_extract_weather,
        provide_context=True,
        doc_md="""
        ### Extract Weather Task
        Calls `run_extraction()` from `scripts/extract_weather.py`.
        Fetches current weather for London, New York, and Tokyo
        from the Open-Meteo API and stores results in SQLite.
        """,
    )

    # ── Task 2: Log a summary of what was extracted ───────────
    log_summary = PythonOperator(
        task_id="log_summary",
        python_callable=task_log_summary,
        provide_context=True,
        doc_md="""
        ### Log Summary Task
        Reads the XCom result from the extract task and writes
        a structured summary to the Airflow task logs.
        """,
    )

    # ── Pipeline order: extract → log summary ─────────────────
    extract_weather >> log_summary
