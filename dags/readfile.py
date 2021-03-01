import json
import pprint
import requests

with open('/Users/rajnigam/workspace/airflow-launch-app/launches.json') as f:
    data = json.load(f)
    image_urls = [result['image'] for result in data['results'] if result['image'] is not None]
    for image_url in image_urls:
        pprint.pprint(image_url)
        response = requests.get(image_url)
        file_name = image_url.split("/")[-1]
        target_file = f"tmp/images/{file_name}"
        with open(target_file, "wb") as f:
            f.write(response.content)
        print(f"download {image_url} to {target_file}")