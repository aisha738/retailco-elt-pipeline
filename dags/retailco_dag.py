from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

# The brief requires minimum 2 retries with exponential backoff
default_args = {
    'owner': 'data_engineering_team',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1), # Set in the past to allow for backfilling
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=2),
    'retry_exponential_backoff': True,
}

# Define the DAG
with DAG(
    'retailco_master_pipeline',
    default_args=default_args,
    description='End-to-End ELT Pipeline for RetailCo',
    schedule_interval='@daily',
    catchup=False, # Set to False to prevent it from automatically running hundreds of times on startup
    tags=['retailco', 'production'],
) as dag:

    # 1. EXTRACT
    # We use BashOperator to run the python scripts we already built.
    # Because we mounted our folder to /opt/airflow in Docker, that is where our files live.
    task_extract = BashOperator(
        task_id='extract_erp_to_lake',
        bash_command='python /opt/airflow/extractor.py',
    )

    # 2. LOAD
    task_load = BashOperator(
        task_id='load_lake_to_warehouse',
        bash_command='python /opt/airflow/loader.py',
    )

# 3. DBT SNAPSHOT (SCD2 History)
    task_dbt_snapshot = BashOperator(
        task_id='dbt_snapshot_dimensions',
        bash_command='cd /opt/airflow/retailco_models && dbt snapshot --profiles-dir .',
    )

    # 4. DBT STAGING
    task_dbt_staging = BashOperator(
        task_id='dbt_run_staging',
        bash_command='cd /opt/airflow/retailco_models && dbt run --select staging --profiles-dir .',
    )

    # 5. DBT MARTS
    task_dbt_marts = BashOperator(
        task_id='dbt_run_marts',
        bash_command='cd /opt/airflow/retailco_models && dbt run --select marts --profiles-dir .',
    )

    # 6. DBT TEST
    task_dbt_test = BashOperator(
        task_id='dbt_test_quality',
        bash_command='cd /opt/airflow/retailco_models && dbt test --profiles-dir .',
    )
    # Define the exact dependency sequence requested by the brief
    # The bitshift operator (>>) tells Airflow: "Task A must succeed before Task B starts"
    task_extract >> task_load >> task_dbt_snapshot >> task_dbt_staging >> task_dbt_marts >> task_dbt_test
