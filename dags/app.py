import json
import pprint
import requests
import pathlib

import airflow
from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from airflow.operators.python_operator import PythonOperator

dag = DAG(
    dag_id="download_launch_data",
    start_date=airflow.utils.dates.days_ago(14),
    schedule_interval="@daily"
)

download_launch = BashOperator(
    task_id="download_launches",
    bash_command="curl -X GET 'https://ll.thespacedevs.com/2.0.0/launch/' -o /tmp/launches.json",
    dag=dag,
)

def _get_pictures():
    pathlib.Path("/tmp/images").mkdir(parents=True, exist_ok=True)
    with open("/tmp/launches.json") as f:
        data = json.load(f)
        image_urls = [result['image'] for result in data['results'] if result['image'] is not None]
        for image_url in image_urls:
            pprint.pprint(image_url)
            response = requests.get(image_url)
            file_name = image_url.split("/")[-1]
            target_file = f"/tmp/images/{file_name}"
            with open(target_file, "wb+") as f:
                f.write(response.content)
            print(f"download {image_url} to {target_file}")

get_pictures = PythonOperator(
    task_id="get_pictures",
    python_callable=_get_pictures,
    dag=dag
)