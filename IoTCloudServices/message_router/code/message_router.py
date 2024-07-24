import paho.mqtt.client as mqtt
import os
import time
import random
import json
import threading
import requests
from flask import Flask, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

from telemetry_register_interface import *
from vehicles_register_interface import *


global client

def on_connect(client, userdata, flags, rc):
    # print the message received from the broker
    print(userdata, flags)
    print("Connected with result code " + str(rc))
    if rc == 0:
        STATE_TOPIC = "/fic/vehicles/+/state/+"
        client.subscribe(STATE_TOPIC)   
        print("Subscribed to ", STATE_TOPIC)

def on_message(client, userdata, msg):
    topic = (msg.topic).split('/')
    if topic[-1] == "request_plate":
        #id_json = '{"vehicle_id":"' + msg.payload.decode() + '"}'
        id_json = {"vehicle_id": msg.payload.decode()}
        json_reply, success = register_vehicle(id_json)
        if not success:
            print("!!!!!!!!!!!!!!!!!!Error registering vehicle!!!!!!!!!!!!!!!!")
        msg_payload = json.dumps(json_reply) # necessary?
        print(msg_payload)
        # the json reply should look like plate_json = '{"plate":"' + plate + '"}'
        client.publish("/fic/vehicles/" + msg.payload.decode() + "/config", payload=msg_payload, qos=1, retain=False)
        print("PUBLISHED! Plate sent to vehicle " + msg.payload.decode())


    elif topic[-1] == "telemetry":
        #append the vehicle telemetry of the message into a json file and print the telemetry in the console
        telemetry = json.loads(msg.payload.decode())
        print("Telemetry received from vehicle " + telemetry["vehicle_plate"])
        json_reply, success = register_telemetry(telemetry)
        if not success:
            print("!!!!!!!!!!!!!!!!!!Error registering telemetry!!!!!!!!!!!!!!!!")
        print("Telemetry registered")
        

    elif topic[-1] == "disconnect":
        data = json.loads(msg.payload.decode())
        print("Vehicle " + data["id"] + " disconnected")
        delete_vehicle(data)
        return

    
    elif topic[-1] == "route_completed":
        data = json.loads(msg.payload.decode())
        print("vehicle " + data["plate"] + " has completed the route at " + data["timestamp"])
        json_reply, success = status_zero(data)
        if success:
            print("vehicle status is now 0")
        else:
            print("Error setting vehicle status to 0")
        return
        
"""
{
  "id": "ed7a05Sibb46",
  "vehicle_plate": "",
  "current_position": {
    "latitude": 0.0,
    "longitude": 0.0
  },
  "current_speed": 0,
  "current_steering": 90.0,
  "current_braking": false,
  "current_leds": [
    {
      "Color": "White",
      "Intensity": 100.0,
      "Blinking": "False"
    },
    {
      "Color": "White",
      "Intensity": 100.0,
      "Blinking": "False"
    },
    {
      "Color": "Red",
      "Intensity": 50.0,
      "Blinking": "False"
    },
    {
      "Color": "Red",
      "Intensity": 50.0,
      "Blinking": "False"
    }
  ],
  "current_ldr": 2834.2164918230424,
  "current_obstacle_distance": 31.085760787067795
}

"""
@app.route("/routes/send/", methods=["POST"])
def send_route():
  """
    {
        "plate": "",
        "vehicle_id": < dynamic >,
        "origin": "Navalcarnero",
        "destination": "Carranque"
    }
  """
  data = request.get_json()
  print(f"Received route in message router: {data}")
  route = {"origin": data["origin"], "destination": data["destination"]}
  route_payload = json.dumps(route)
  result = client.publish("/fic/vehicles/" + data["vehicle_id"] + "/routes", payload= route_payload, qos=1, retain=False)
  # check if the message is correctly received by the vehicle
  if result.rc == 0:
    return {"result": "Route sent to vehicle"}, 201
  else:
    return {"result": "Error sending route to vehicle"}, 500




def mqtt_thread():
    global client
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
    client.username_pw_set(username="fic_server", password="fic_password")
    
    client.on_connect = on_connect
    client.on_message = on_message
  

    MQTT_SERVER = os.getenv("MQTT_SERVER_ADDRESS")
    MQTT_PORT = int(os.getenv("MQTT_SERVER_PORT"))
    client.connect(MQTT_SERVER, MQTT_PORT, 60)
    client.loop_forever()

    

if __name__ == "__main__":
    t1 = threading.Thread(target=mqtt_thread, daemon=True)
    t1.start()

    API_HOST = os.getenv("HOST")
    API_PORT = int(os.getenv("PORT"))
    app.run(host=API_HOST, port=API_PORT, debug=False)