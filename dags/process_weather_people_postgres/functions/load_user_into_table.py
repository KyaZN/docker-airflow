import logging
from airflow.providers.postgres.hooks.postgres import PostgresHook


def load_user_into_table(id, **context):  
    file_path = f'/tmp/user_inputttt_{id}.csv'
    pg_hook = PostgresHook()
    pg_hook.bulk_load(context["templates_dict"]["table_name"], file_path)
    logging.info("The data was loaded successfully.")