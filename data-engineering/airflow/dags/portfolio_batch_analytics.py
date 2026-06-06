from datetime import datetime
from airflow import DAG
from airflow.operators.bash import BashOperator

with DAG(
    dag_id="portfolio_batch_analytics",
    start_date=datetime(2026, 1, 1),
    schedule="@daily",
    catchup=False,
    tags=["finance", "spark", "portfolio"],
) as dag:
    run_spark = BashOperator(
        task_id="run_portfolio_aggregation",
        bash_command="spark-submit /opt/airflow/jobs/portfolio_aggregation.py",
    )
