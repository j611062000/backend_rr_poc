from datetime import datetime

import requests

from flask import Flask, request, jsonify
from requests import Response, RequestException

from env import Env
from util import RoundRobin as rr, Api, get_response_time_ms


class NoHealthyUpstream(RequestException, ValueError):
    pass


app = Flask(__name__)
app.debug = True  # Enable debug mode

app_instances: list[str] = Env.app_instances

rr.init(len(app_instances))


def get_resp(response: Response, reason: str, cur_idx: int):
    if response.status_code == 200:
        # Update the instance index for the next request (round-robin)
        response_data = Api.get_response("success", response, reason, cur_idx)
        return jsonify(response_data), 200  # Respond with the instance response
    else:
        response_data = Api.get_response("error", response, reason, cur_idx)
        return jsonify(response_data), 500  # Respond with an error if upstream call failed


def get_rr_idx_instances():
    # Get the current instance address based on round-robin index
    current_instance_index, reason = rr.get_instance_index()
    if current_instance_index == -1:
        raise NoHealthyUpstream("No healthy upstream")
    current_instance: str = app_instances[current_instance_index]
    return current_instance, current_instance_index, reason


@app.route('/', methods=['POST'])
def round_robin(inject_post=None):
    post = inject_post if inject_post else requests.post
    # Send the received JSON payload to the selected instance

    current_instance_index = -1
    current_instance = 0
    try:
        current_instance, current_instance_index, reason = get_rr_idx_instances()
        data = request.get_json()  # Get the JSON data from the POST request
        start: datetime = datetime.now()
        response: Response = post(current_instance, json=data, timeout=Env.app_api_timeout_seconds)
        resp_time = get_response_time_ms(start)
        resting_reason = rr.update_response_time(current_instance_index, resp_time)

        return get_resp(response, reason + resting_reason, current_instance_index)

    except requests.exceptions.Timeout:
        rr.update_response_time(current_instance_index, Env.app_api_timeout_ms)
        reason = f"timeout when sending request to {current_instance} | so we add resting number {Env.timeout_rest} onto {current_instance_index}"
        response_data = Api.get_response("failed", None, reason, current_instance_index)
        return jsonify(response_data), 500  # Respond with an error for any exception

    except requests.RequestException as e:
        reason = f"{e}"
        response_data = Api.get_response("failed", None, reason, current_instance_index)
        return jsonify(response_data), 500  # Respond with an error for any exception


if __name__ == '__main__':
    print(f"Starting app with config: \n"
          f"slow_down_threshold_ms = {Env.slow_down_threshold_ms} \n"
          f"app_api_timeout_ms = {Env.app_api_timeout_ms} \n"
          f"rest_numer = {rr.resting_number} \n"
          f"env = {Env.env} \n"
          )
    app.run(host='0.0.0.0', port=5000, debug=True)  # Run the Round Robin API on port 20001
