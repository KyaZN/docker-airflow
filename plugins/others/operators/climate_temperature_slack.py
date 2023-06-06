import logging
import requests
import json

from airflow.models.baseoperator import BaseOperator

from airflow.exceptions import AirflowException
from airflow.providers.slack.operators.slack_webhook import SlackWebhookOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook


class ClimateNotificationSlackOperator(BaseOperator):
    
    def __init__(self,
                slack_conn: str = None,
                pg_conn: str = None,
                message: str = '',
                icon_emoji: str = None,
                table_name: str = None,
                endpoint_fixed: str = None,
                *args,
                **kwargs
            ):
        super().__init__(*args, **kwargs)
        #super(RowCountToSlackChannelOperator, self).__init__(*args, **kwargs)

        self.slack_conn = slack_conn
        self.pg_conn = pg_conn
        self.message = message
        self.icon_emoji = icon_emoji
        self.table_name = table_name
        self.channel='#airflow-weather_alerts'
        self.endpoint_fixed = endpoint_fixed
        self.sql=None
    
    def get_weather(self, endpoint_added):    
        url = endpoint_added
        response = requests.get(url=url).json()
        
        temp_kevin = response['main']['temp']
        temp_celsius = temp_kevin - 273.15

        return temp_celsius 

    def execute(self, context):
        if not isinstance(self.table_name, str):
            raise AirflowException(f"Argument 'table_name' of type {type(self.table_name)} is not a string.")
        if not isinstance(self.table_predicate, str):
            raise AirflowException(f"Argument 'table_predicate' of type {type(self.table_name)} is not a string.")
        
        pg_hook = None
        if self.pg_conn:
            pg_hook = PostgresHook(self.pg_conn)
        else:
            pg_hook = PostgresHook()
        
        conn = pg_hook.get_conn()
        cursor = conn.cursor()
        self.sql = f""" SELECT id, city, lat, lon FROM {self.table_name} """
        cursor.execute(self.sql)
        rows = cursor.fetchall()
        
        for row in rows:
            logging.info(row)

            endpoint_with_params = self.endpoint_fixed + f'&lat={row[2]}&lon={row[3]}'

            celsius = self.get_weather(endpoint_with_params)
            message_info = f'El clima en {row[1]} es de {celsius}C°'
        
            slack_alert = SlackWebhookOperator(
                task_id=f"slack_weather_info_alert_for{row[0]}",
                slack_webhook_conn_id = self.slack_conn,
                message=message_info,
                channel=self.channel
            )
        
            slack_alert.execute(context=context)
        
        
       