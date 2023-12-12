import threading
import random
from time import sleep

from flask import Flask, request, jsonify


class Status:
    Normal = 0
    Slow = 1
    Down = 2


app = Flask(__name__)
port = 5000
global current_status


@app.route('/', methods=['POST'])
def echo_request():
    data = request.get_json()  # Get the JSON data from the POST request
    if current_status == Status.Slow:
        sleep(random.randint(1, 5))
    elif current_status == Status.Down:
        sleep(1000000)
    return jsonify(data), 200  # Respond with the received JSON payload


@app.route('/health', methods=['GET'])
def health():
    return jsonify("all good!"), 200


@app.route('/update_status', methods=['POST'])
def update_status():
    data = request.get_json()["status"]
    global current_status
    try:
        current_status = int(data)
        if current_status < 0 or current_status > 2:
            return jsonify("invalid status"), 400
    except:
        current_status = Status.Normal

    return jsonify("successfully updated status as {}".format(current_status)), 200


if __name__ == '__main__':
    current_status = Status.Normal
    app.run(host='0.0.0.0', port=port, debug=True)  # Run the Round Robin API on port 20001
