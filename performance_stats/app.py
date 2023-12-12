import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import schedule
import redis
import asyncio

import requests
from requests import Response

app_instances: list[str] = [
    "http://localhost:10001",
    # "http://application_api_2:5000",
    # "http://application_api_3:5000"
]

lock = threading.Lock()
global r
r = redis.StrictRedis(host='localhost', port=6379, db=0)


# Function to simulate getting response time from Application API
async def get_response_time(instance: str) -> float:
    start: datetime = datetime.now()
    _: Response = requests.post(instance, json={})
    return int((datetime.now() - start).total_seconds() * 1000)


# Scheduler function to poll and save response times
async def poll_and_save():
    tasks = [get_response_time(instance) for instance in app_instances]
    responses = await asyncio.gather(*tasks)
    for idx, response in enumerate(responses):
        await r.set(str(idx), response)
        print(f"instance {idx} Response Time: {r.get(str(idx))}")


if __name__ == '__main__':
    while True:
        asyncio.run(poll_and_save())
        time.sleep(1)  # Adjust sleep time as needed to reduce CPU usage
