#!/usr/bin/env python
import rospy
import time
import json
from messages.msg import TargetSystemData, ReconfigurationCommand
from flask import Flask, request, jsonify

app = Flask(__name__)
 
# Initialize ROS node
rospy.init_node('listener', anonymous=True)

# Global variable 
adaptation_options = None
result = None
monitor_schema = None
extract_schema = False
reconfigure_schema = None

################JSON Schema extractor helper fucntion /monitor_schema###############
def extract_json_schema(data):
    if isinstance(data, dict):
        schema = {
            "type": "object",
            "properties": {},
        }
        for key, value in data.items():
            schema["properties"][key] = extract_json_schema(value)
        if len(schema["properties"]) == 0:
            del schema["properties"]
        return schema
    elif isinstance(data, list):
        schema = {
            "type": "array",
            "items": extract_json_schema(data[0]),
        }
        return schema
    else:
        if isinstance(data, str):
            data = '"' + data + '"'
        return {
            "type": type(data).__name__,
        }  # Remove the 'default' field

###########This is Function for the /monitor and /monitor_schema endpoints##############
def monitor_callback(data):
    # Process the raw serialized data here

    response = {
      "ecg": {
        "Batt": data.ecg_batt,
        "Risk": data.ecg_risk,
        "Data": data.ecg_data
    },
    "abps": {
        "Batt": data.abps_batt,
        "Risk": data.abps_risk,
        "Data": data.abps_data
    },
    "trm": {
        "Batt": data.trm_batt,
        "Risk": data.trm_risk,
        "Data": data.trm_data
    },
    "abpd": {
        "Batt": data.abpd_batt,
        "Risk": data.abpd_risk,
        "Data": data.abpd_data
    },
    "oxi": {
        "Batt": data.oxi_batt,
        "Risk": data.oxi_risk,
        "Data": data.oxi_data
    },
    "glc": {
        "Batt": data.glc_batt,
        "Risk": data.glc_risk,
        "Data": data.glc_data
    }                                   
    }

    global result,monitor_schema,extract_schema
    result = response
    # Set the flag to extract the schema
    if extract_schema:
        monitor_schema = extract_json_schema(response)
        extract_schema = False  # Reset the flag after extraction
        return monitor_schema
    return response


######This function is for the /adaptation_options and /adaptation_options_schema########
def reconfigure_callback(data):
    global adaptation_options,reconfigure_schema,extract_schema
        

    # Initialize an empty dictionary to store sensor-specific reconfiguration events
    if adaptation_options is None:
        adaptation_options = {}

    # Extract the sensor ID from the target field
    sensor_id = data.target.split("/")[-1]

    # Initialize an empty list for the sensor's reconfiguration events
    if sensor_id not in adaptation_options:
        adaptation_options[sensor_id] = []

    # Check if the sensor's reconfiguration list is empty
    if not adaptation_options[sensor_id]:
        adaptation_options[sensor_id].append({
            "source": data.source,
            "target": data.target,
            "action": data.action
        })
        return adaptation_options

    # Limit the list size to the last 7 events for each sensor
    adaptation_options[sensor_id] = adaptation_options[sensor_id][-8:]
    if extract_schema:
        reconfigure_schema = extract_json_schema(adaptation_options)
        extract_schema = False  # Reset the flag after extraction
        return reconfigure_schema
    return adaptation_options


########################### A -- P  --  I ##########################################


######################### MONITOR

#ENDPOINT:localhost:5000/monitor
@app.route("/monitor", methods=["GET"])
def get_data():
    global result

    # Subscribe to the TargetSystemData topic when a request is made
    rospy.Subscriber("TargetSystemData", TargetSystemData, monitor_callback)

    # Wait for the callback function to process data before returning
    while result is None:
        return "processing...."
        time.sleep(0.1)

    # Return the processed data
    response_copy = result
    result= None  # Clear the global variable for the next request
    return jsonify(response_copy)



#ENDPOINT:localhost:5000/monitor_schema
@app.route("/monitor_schema", methods=["GET"])
def get_monitor_schema():
    global extract_schema,monitor_schema

    # Set the flag to extract the schema
    extract_schema = True

    # Call the monitor_callback function to trigger schema extraction
    get_data()

    # Wait for the schema to be extracted
    while monitor_schema is None:
        return "processing...."
        time.sleep(0.1)

    # Return the JSON schema and reset the flag
    response_copy = monitor_schema
    monitor_schema = None  # Clear the global variable for the next request
    extract_schema = False  # Reset the flag

    return jsonify(response_copy)

######################### ADAPTATION OPTIONS

#ENDPOINT:localhost:5000/adaptation_options
@app.route("/adaptation_options", methods=["GET"])
def get_all_adaptation_options():
    global adaptation_options

    # Subscribe to the reconfigure topic
    rospy.Subscriber('reconfigure', ReconfigurationCommand, reconfigure_callback)
    

     # Wait for the callback function to process data before returning
    while adaptation_options is None:
        return "processing...."
        time.sleep(0.1)

    # Return the processed data
    response_copy = adaptation_options
    adaptation_options= None  # Clear the global variable for the next request
    return jsonify(response_copy)


# Endpoint: /adaptation_options/<sensor_id>
@app.route("/adaptation_options/<sensor_id>", methods=["GET"])
def get_sensor_adaptation_options(sensor_id):
    global adaptation_options

    # Subscribe to the reconfigure topic
    rospy.Subscriber('reconfigure', ReconfigurationCommand, reconfigure_callback)

    # Wait for the callback function to process data before returning
    while adaptation_options is None:
        return "processing...."
        time.sleep(0.1)

    # Filter the adaptation options based on the sensor ID
    sensor_options = adaptation_options.get(sensor_id, [])
    
    # Return the filtered adaptation options
    adaptation_options= None  # Clear the global variable for the next request
    return jsonify(sensor_options)
    
#ENDPOINT:localhost:5000/adaptation_options_schema
@app.route("/adaptation_options_schema", methods=["GET"])
def adaptation_option_schema():
    global reconfigure_schema,extract_schema

    # Set the flag to extract the schema
    extract_schema = True

    # Call the reconfigure_callback function to trigger schema extraction
    get_all_adaptation_options()

    # Wait for the schema to be extracted
    while reconfigure_schema is None:
        return "processing...."
        time.sleep(0.1)

    # Return the JSON schema and reset the flag
    response_copy = reconfigure_schema
    reconfigure_schema = None  # Clear the global variable for the next request
    extract_schema = False  # Reset the flag

    return jsonify(response_copy)
    
    

if __name__ == '__main__':
    app.run(debug=True)