#!/usr/bin/env python
import threading
from flask import Flask, request, jsonify
from listener import monitor_callback, reconfigure_callback

app = Flask(__name__)

# Initialize ROS node
rospy.init_node('server', anonymous=True)

# Global variables
result = None
adaptation_options = None

# Create a thread pool with a fixed number of workers
thread_pool = []
for _ in range(10):  # Adjust the number of workers as needed
    thread = threading.Thread(target=worker_function)
    thread.start()
    thread_pool.append(thread)

# Define a global variable to track the current worker index
current_worker_index = 0

def worker_function():
    while True:
        # Wait for a request to be assigned
        request = wait_for_request()

        # Process the request
        process_request(request)

def round_robin_assignment():
    global current_worker_index

    # Get the next available worker index
    worker_index = current_worker_index
    current_worker_index += 1
    current_worker_index %= len(thread_pool)

    # Return the worker instance
    return thread_pool[worker_index]

# Endpoint: /monitor
@app.route("/monitor", methods=["GET"])
def get_data():
    # Assign the request to a worker using round robin
    worker = round_robin_assignment()

    # Wait for the worker to process the request and return the result
    result = worker.get_result()
    return jsonify(result)

# Endpoint: /adaptation_options
@app.route("/adaptation_options", methods=["GET"])
def get_all_adaptation_options():
    # Assign the request to a worker using round robin
    worker = round_robin_assignment()

    # Wait for the worker to process the request and return the result
    adaptation_options = worker.get_result()
    return jsonify(adaptation_options)


if __name__ == '__main__':
    app.run(debug=True)

