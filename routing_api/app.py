import os
from datetime import datetime
from typing import List
import requests
from flask import Flask, request, jsonify
from requests import Response

app = Flask(__name__)
app.debug = True  # Enable debug mode


def safe_get_env_var_as_int(var_name: str, default_val: int = 0) -> int:
    try:
        return int(os.getenv(var_name))
    except:
        return default_val


slow_down_threshold_ms = safe_get_env_var_as_int('SLOW_DOWN_THRESHOLD_MS')
app_api_timeout_ms = safe_get_env_var_as_int('APP_API_TIMEOUT_MS')
upstream_port = safe_get_env_var_as_int('UPSTREAM_PORT')
slow_down_rest_number = safe_get_env_var_as_int('SLOW_DOWN_REST_NUMBER')
timeout_rest_number = safe_get_env_var_as_int('TIMEOUT_REST_NUMBER')

# List of Application API instances (add addresses/ports accordingly)
# app_instances: List[str] = [
#     f"http://application_api_1:{upstream_port}",
#     f"http://application_api_2:{upstream_port}",
#     f"http://application_api_3:{upstream_port}"
# ]

# List of Application API instances (add addresses/ports accordingly)
app_instances: List[str] = [
    f"http://localhost:10001",
    f"http://localhost:10002",
    f"http://localhost:10003"
]


current_instance_index: int = 0  # To track the current instance index
response_time_ms_statistics: list[int] = [0 for _ in range(len(app_instances))]
resting_number: list[int] = [0 for _ in range(len(app_instances))]


def update_resting_number(rest_numbers: list[int], idx: int, cnt: int) -> None:
    cur_numer = rest_numbers[idx]
    new_numer = cur_numer + cnt
    if new_numer < 0:
        rest_numbers[idx] = 0
    else:
        rest_numbers[idx] = new_numer


def get_instance_index(cur_idx: int, resp_time_stat: list[int], rest_numbers: list[int], total_srv_number: int) -> int:
    cur_idx = (cur_idx + 1) % total_srv_number
    visited = 0

    while visited < total_srv_number:
        print("get_instance_index",rest_numbers[visited], cur_idx)
        update_resting_number(rest_numbers, cur_idx, -1)
        if rest_numbers[cur_idx] == 0:
            return cur_idx
        visited += 1
        cur_idx += 1

    return resp_time_stat.index(min(resp_time_stat))


def update_response_time(cur_idx: int, resp_time_stat: list[int], resp_time_ms: int) -> None:
    resp_time_stat[cur_idx] = resp_time_ms

    if slow_down_threshold_ms <= resp_time_ms < app_api_timeout_ms:
        update_resting_number(resting_number, cur_idx, slow_down_rest_number)
    elif resp_time_ms >= app_api_timeout_ms:
        update_resting_number(resting_number, cur_idx, timeout_rest_number)


@app.route('/', methods=['POST'])
def round_robin():
    global current_instance_index

    # Get the current instance address based on round-robin index
    current_instance_index = get_instance_index(current_instance_index, response_time_ms_statistics, resting_number,
                                                len(app_instances))
    current_instance: str = app_instances[current_instance_index]

    # Send the received JSON payload to the selected instance
    try:
        data = request.get_json()  # Get the JSON data from the POST request
        start: datetime = datetime.now()
        response: Response = requests.post(current_instance, json=data, timeout=app_api_timeout_ms // 1000)
        resp_time = int((datetime.now() - start).total_seconds() * 1000)
        update_response_time(current_instance_index, response_time_ms_statistics, resp_time)

        if response.status_code == 200:
            # Update the instance index for the next request (round-robin)
            response_data = {
                "status": "success",
                "data_from_upstream": response.json(),
                "upstream_index": current_instance_index + 1,
                "upstream_service": current_instance,
                "response_time_ms_statistics": response_time_ms_statistics,
                "rest_number": resting_number,
            }
            return jsonify(response_data), 200  # Respond with the instance response
        else:
            return jsonify({
                "error": "Upstream API failed",
                "upstream_index": current_instance_index
            }
            ), 500  # Respond with an error if upstream call failed
    except requests.exceptions.Timeout as timeout_error:
        update_response_time(current_instance_index, response_time_ms_statistics, app_api_timeout_ms)
        return jsonify({
            "error": f"Request Exception: {timeout_error}",
            "current_instance_index": current_instance_index,
            "response_time_ms_statistics": response_time_ms_statistics,
            "app_api_timeout_ms": app_api_timeout_ms
        }), 500  # Respond with an error for any exception

    except requests.RequestException as e:
        return jsonify({"error": f"Request Exception: {e}"}), 500  # Respond with an error for any exception


if __name__ == '__main__':
    print(f"Starting app with config: \n"
          f"slow_down_threshold_ms = {slow_down_threshold_ms} \n"
          f"app_api_timeout_ms = {app_api_timeout_ms} \n"
          f"rest_numer = {resting_number} \n"
          )
    app.run(host='0.0.0.0', port=5000, debug=True)  # Run the Round Robin API on port 20001
