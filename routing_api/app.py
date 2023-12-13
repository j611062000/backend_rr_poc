from datetime import datetime
from typing import Callable
import requests
from flask import Flask, request, jsonify
from requests import Response
from util import RoundRobin as rr, Api, get_response_time_ms
from env import Env

app = Flask(__name__)
app.debug = True  # Enable debug mode

app_instances: list[str] = Env.app_instances

rr.init(len(app_instances))


def get_resp(response: Response):
    if response.status_code == 200:
        # Update the instance index for the next request (round-robin)
        response_data = Api.get_success_response(response)
        return jsonify(response_data), 200  # Respond with the instance response
    else:
        return jsonify({
            "error": "Upstream API failed",
            "upstream_index": rr.cur_idx
        }), 500  # Respond with an error if upstream call failed


@app.route('/', methods=['POST'])
def round_robin(inject_post=None):
    # Get the current instance address based on round-robin index
    current_instance_index = rr.get_instance_index()
    current_instance: str = app_instances[current_instance_index]

    post = inject_post if inject_post else requests.post

    # Send the received JSON payload to the selected instance
    try:
        data = request.get_json()  # Get the JSON data from the POST request
        start: datetime = datetime.now()
        response: Response = post(current_instance, json=data, timeout=Env.app_api_timeout_seconds)
        resp_time = get_response_time_ms(start)
        rr.update_response_time(current_instance_index, resp_time)

        return get_resp(response)

    except requests.exceptions.Timeout as timeout_error:
        rr.update_response_time(current_instance_index, Env.app_api_timeout_ms)
        return jsonify({
            "error": f"Request Exception: {timeout_error}",
            "current_instance_index": current_instance_index,
            "response_time_ms_statistics": rr.resp_time_stat,
            "app_api_timeout_ms": Env.app_api_timeout_ms
        }), 500  # Respond with an error for any exception

    except requests.RequestException as e:
        return jsonify({"error": f"Request Exception: {e}"}), 500  # Respond with an error for any exception


if __name__ == '__main__':
    print(f"Starting app with config: \n"
          f"slow_down_threshold_ms = {Env.slow_down_threshold_ms} \n"
          f"app_api_timeout_ms = {Env.app_api_timeout_ms} \n"
          f"rest_numer = {rr.resting_number} \n"
          f"env = {Env.env} \n"
          )
    app.run(host='0.0.0.0', port=5000, debug=True)  # Run the Round Robin API on port 20001
