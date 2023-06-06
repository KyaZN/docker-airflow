# TODO: Remove the directories, code, libraries and all the things are not necessary for your dag. 
# Checklist:
# - Remove imports you don't need.
# - Remove folders you don't need.
# - Remove unnecessary operators. (e.g. HelloWorld python operator)
# - Create technical documentation in confluence.
# - Create optional user-guide documentation.
# - Be sure to update the dag_config yaml file with schedules for the environments you need.
# - Be sure to update the pipeline_config yaml file if needed.
# - Be sure to update the README.md file.
# - Don't forget to remove this commented block at the end.

import logging
import os
from datetime import date, datetime, timedelta

from utils.common import get_config
from utils.common import get_md
from utils.common import get_sql


from airflow import DAG
from airflow.models import Variable
from airflow.operators.dummy_operator import DummyOperator
from airflow.operators.python_operator import PythonOperator
from airflow.providers.http.sensors.http import HttpSensor
from airflow.providers.http.operators.http import SimpleHttpOperator
from airflow.utils.trigger_rule import TriggerRule
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.providers.slack.operators.slack_webhook import SlackWebhookOperator

from airflow.utils.task_group import TaskGroup


# Importing python functions
from process_weather_people_postgres.functions.get_user import get_user
from process_weather_people_postgres.functions.load_user_into_table import load_user_into_table
from process_weather_people_postgres.functions.load_user_into_table import load_user_into_table
from others.operators.climate_temperature_slack import ClimateNotificationSlackOperator


# Declare configuration variables
dag_file_name = os.path.basename(__file__).split('.')[0]
dag_config = get_config(dag_file_name = dag_file_name, config_filename = 'dag_config.yaml')
pipeline_config = get_config(dag_file_name = dag_file_name, config_filename = 'pipeline_config.yaml')

env=os.getenv('ENVIRONMENT')
default_arguments = dag_config['default_args'][env]

# Getting variables of pipeline configs
endpoint_weather = pipeline_config['endpoint_weather']
endpoint_users = pipeline_config['endpoint_users']

#Airflow docstring
doc_md = get_md(dag_file_name, 'README.md')

#logging.basicConfig(level=logging.INFO)

#Declare DAG insrtance and DAG operators
with DAG(dag_file_name,
          description='Extract users and validate their locations to estimate their weather forecast',
          start_date=datetime.strptime(dag_config['dag_args'][env]["start_date"], '%Y-%m-%d'),
          max_active_runs=dag_config['dag_args'][env]["max_active_runs"],
          catchup=dag_config['dag_args'][env]["catchup"],
          #max_active_tasks=dag_config['dag_args'][env]["max_active_tasks"], # This is an optional argument, if you don't need it, please remove it.
          tags = [],
          schedule_interval=dag_config['schedule'][env],
          default_args=default_arguments,
          dagrun_timeout=timedelta(hours=dag_config["dag_run_timeout"]),
          doc_md=doc_md,
          ) as dag:
    
    ##### DECLARING THE OPERATORS ######
    
    # Declare Dummy Operators
    start = DummyOperator(task_id='start')
    end = DummyOperator(task_id='end')

    ############  PEOPLE DATA
    create_users_table = PostgresOperator(
        task_id='create_users_table',
        sql=get_sql(dag_file_name, 'create_users_table.sql'),
        params={"table_name": "bronze.user"}
    )
    
    ############  WEATHER DATA
    # create_basic_data_table = PostgresOperator(
    #     task_id='create_weather_table',
    #     sql=get_sql(dag_file_name, 'create_weather_table.sql'),
    #     params={"table_name": "bronze.basic_data"}
    # )

    #api.openweathermap.org/data/2.5/weather?id=524901&appid=c24cd5d9e02aaefaa18ab6d53b9956bclat=58.3934&lon=-63.2743

    with TaskGroup('group_users') as group_users:
        for i in range(1,2):
            is_api_available = HttpSensor(
                task_id=f"is_{i}_api_available",
                http_conn_id ="random_people_api",
                endpoint="api/",
                poke_interval=60*5, # Wait 5 minutes until next retry.
                timeout=60*60*1, # Trigger a timeout exception after 1 hour.
                mode="poke"
            )

            getting_user = PythonOperator(
                task_id=f'get_{i}_user',
                python_callable=get_user,
                op_args=[i, endpoint_users]
            )

            load_user_table = PythonOperator(
                task_id=f'load_{i}_user_into_table',
                python_callable=load_user_into_table,
                op_args=[i],
                templates_dict={
                    "table_name": 'bronze.user'
                }
            )

            weather_notification = ClimateNotificationSlackOperator(
                task_id=f'slack_notification_{i}',
                slack_conn='slack_connection_airflow',
                message='El area de marketing ya puede usar la información',
                table_name='bronze.user',
            )

            create_users_table >> is_api_available >> getting_user >> load_user_table >> weather_notification
    

    start >> create_users_table >> group_users >> end