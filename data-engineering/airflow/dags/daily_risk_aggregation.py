from datetime import datetime
from airflow import DAG
from airflow.operators.bash import BashOperator
with DAG('daily_risk_aggregation', start_date=datetime(2026,1,1), schedule='@daily', catchup=False) as dag:
    BashOperator(task_id='run_spark_risk_job', bash_command='echo Running PySpark risk aggregation')
