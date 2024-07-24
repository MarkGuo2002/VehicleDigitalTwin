import time
import os
import paho.mqtt.client as mqtt
import threading
import requests
import random
import json
from datetime import datetime
import subprocess
from math import radians, cos, sin, acos

global vehicle_plate
vehicle_plate = ""

global event_message
event_message = ""

def get_host_name():
    bashCommandName = 'echo $HOSTNAME'
    host = subprocess.check_output(['bash','-c', bashCommandName]).decode("utf-8").strip()
    return host


STATE_TOPIC = "/fic/vehicles/" + get_host_name() + "/state"
CONFIG_TOPIC = "/fic/vehicles/" + get_host_name() + "/config"
PLATE_REQUEST_TOPIC = "/fic/vehicles/" + get_host_name() + "/state/request_plate"
ROUTES_TOPIC = "/fic/vehicles/" + get_host_name() + "/routes"

global client

global routes 
routes = []
#routes = [{"Origin": "Comisaría de Policía de Leganés", "Destination": "Universidad Carlos III de Madrid - Campus de Leganés"}]


global current_braking
current_braking = False

global current_steering
current_steering = 90.0

global current_speed
current_speed = 0

global current_position
current_position = {"latitude": 0.0, "longitude": 0.0}

global current_leds
current_leds = [{"Color": "White", "Intensity": 0.0, "Blinking": "False"},
                        {"Color": "White", "Intensity": 0.0, "Blinking": "False"},
                        {"Color": "Red", "Intensity": 0.0, "Blinking": "False"},
                        {"Color": "Red", "Intensity": 0.0, "Blinking": "False"}]

global current_ldr
current_ldr = 0.0

global current_obstacle_distance
current_obstacle_distance = 0.0

global currentRouteDetailedSteps
currentRouteDetailedSteps = []

global vehicleControlCommands
vehicleControlCommands = []



google_maps_api_key = "AIzaSyCx--8jCyxlt9wa6scscPC0wlwDxBmLeOM"


def vehicle_controller():
    """ """
    global event_message
    global current_braking
    print("Executing vehicle controller thread\n")
    while True:
        try:
            if len(routes) > 0:
                origin_address = routes[0]["origin"]
                destination_address = routes[0]["destination"]
                routes_manager(origin_address, destination_address)
                # print(f"Route commands are: {vehicleControlCommands}\n")

                i = 0
                prev_speed = 0
                while len(vehicleControlCommands) > 0:
                    if prev_speed > vehicleControlCommands[0]["Speed"]:
                        print(f"Braking from speed {prev_speed} to {vehicleControlCommands[0]['Speed']}\n")
                        current_braking = True
                    else:
                        current_braking = False
                    execute_command(vehicleControlCommands[0], currentRouteDetailedSteps[i])
                    i += 1
                    prev_speed = vehicleControlCommands[0]["Speed"]
                    
                    del vehicleControlCommands[0]
                if len(routes) > 0:
                    print("\n================Route completed==================\n")
                    del routes[0]
                    event_message = "Route completed"

                    

            else:
                print("Vehicle stopped and waiting for routes\n")
                vehicle_stop()
                time.sleep(10)
        except KeyboardInterrupt:
            break

def execute_command(command, step):
    global current_steering
    global current_speed
    global current_position
    global vehicleControlCommands
    print("Executing command: {}".format(command))

    print(command["Time"])
    current_steering = command["SteeringAngle"]
    current_speed = command["Speed"]
    # debug()
    time.sleep(float(command["Time"]))
    current_position = step["Destination"]



def routes_manager(origin_address="New York", destination_address="Yonkers"):
    """
    Esta función se encarga de gestionar las rutas que el vehículo
    debe seguir. Para ello, se comunica con el servicio de Google Maps
    para obtener la ruta a seguir. Una vez obtenida la ruta, se
    obtienen los pasos a seguir y se generan los comandos que el
    vehículo debe seguir para completar la ruta.
    """
    global currentRouteDetailedSteps
    global vehicleControlCommands

    # print("Asignando una ruta al vehículo")
    url = \
        "https://maps.googleapis.com/maps/api/directions/json?origin=" + \
        origin_address + "&destination=" + \
        destination_address + "&key=" + google_maps_api_key
    print("conectando a la API URL: {}".format(url))
    time.sleep(1)
    payload = {}
    headers = {}
    response = requests.request("GET", url, headers=headers, data=payload)
    current_route = response.text
    # print("La ruta es: {}".format(response.text))
    steps = response.json()["routes"][0]["legs"][0]["steps"]
    #print(steps)

    get_detailed_steps(steps)
    getCommands()

    #write content of currentRouteDetailedSteps to a file
    with open("currentRouteDetailedSteps.json", "w") as f:
        json.dump(currentRouteDetailedSteps, f)

    # write content of vehicleControlCommands to a file
    with open("vehicleControlCommands.json", "w") as f:
        json.dump(vehicleControlCommands, f)
    print("He acabado de asignar los comandos al vehículo")



def get_detailed_steps(steps):
    """ 
    debe obtener los waypoints que debe
    atravesar el vehículo con el mayor nivel de precisión posible
    """
    global currentRouteDetailedSteps
    for step in steps:
        index = 0
        stepSpeed = (step["distance"]["value"] / 1000) / (step["duration"]["value"] / 3600) 
        stepDistance = step["distance"]["value"]
        stepTime = step["duration"]["value"]
        try:
            stepManeuver = step["maneuver"]
        except:
            stepManeuver = "Straight"
        substeps = decode_polyline(step["polyline"]["points"])
        for substep in substeps:
            if index < len(substeps):
                p1 = {"latitude": substeps[index][0], "longitude": substeps[index][1]}
                p2 = {"latitude": substeps[index + 1][0], "longitude": substeps[index + 1][1]}
                # print("Voy a calcular la distancia entre {} y {}".format(p1, p2))
                points_distance = distance(p1, p2)
                if points_distance > 0.001:
                    subStepDuration = points_distance / (stepSpeed / 3600)
                    new_detailed_step = {
                                         "Origin":      p1,
                                         "Destination": p2,
                                         "Speed":       stepSpeed,
                                         "Time":        subStepDuration,
                                         "Distance":    points_distance,
                                         "Maneuver":    stepManeuver
                                        }
                    # print("Se ha añadido el paso: {}".format(new_detailed_step))
                    currentRouteDetailedSteps.append(new_detailed_step)
    print("La ruta tiene {} pasos".format(len(currentRouteDetailedSteps)))


def getCommands():
    """ 
        responsable de generar los comandos a partir de la secuencia de pasos obtenido.
    """
    global vehicleControlCommands

    steeringAngle: float = 90.0
    vehicleControlCommands = []
    index = 0
    for detailedStep in currentRouteDetailedSteps:
        index += 1
        #print("Generando el comando {} para el paso {}".format(index, detailedStep))
        if (detailedStep["Maneuver"].upper() == "STRAIGHT" or detailedStep["Maneuver"].upper() == "RAMP-LEFT" or detailedStep["Maneuver"].upper() == "RAMP-RIGHT" or detailedStep["Maneuver"].upper() == "MERGE" or detailedStep["Maneuver"].upper() == "MANEUVER-UNSPECIFIED"):
            steeringAngle = 90.0
        if detailedStep["Maneuver"].upper() == "TURN-LEFT":
            steeringAngle = 45.0
        if detailedStep["Maneuver"].upper() == "UTURN-LEFT":
            steeringAngle = 0.0
        if detailedStep["Maneuver"].upper() == "TURN-SHARP-LEFT":
            steeringAngle = 15.0
        if detailedStep["Maneuver"].upper() == "TURN-SLIGHT-LEFT":
            steeringAngle = 60.0
        if detailedStep["Maneuver"].upper() == "TURN-RIGHT":
            steeringAngle = 135.0
        if detailedStep["Maneuver"].upper() == "UTURN-RIGHT":
            steeringAngle = 180.0
        if detailedStep["Maneuver"].upper() == "TURN-SHARP-RIGHT":
            steeringAngle = 105.0
        if detailedStep["Maneuver"].upper() == "TURN-SLIGHT-RIGHT":
            steeringAngle = 150.0
        newCommand = {"SteeringAngle": steeringAngle, "Speed": detailedStep["Speed"], "Time": detailedStep["Time"]}
        vehicleControlCommands.append(newCommand)

def debug():
    print("current_steering: {}".format(current_steering))
    print("current_speed: {}".format(current_speed))
    print("current_position: {}".format(current_position))
    #print("current_leds: {}".format(current_leds))
    # print("current_ldr: {}".format(current_ldr))
    #print("current_obstacle_distance: {}".format(current_obstacle_distance))
    #print("currentRouteDetailedSteps: {}".format(currentRouteDetailedSteps))
    #print("vehicleControlCommands: {}".format(vehicleControlCommands))
    #print("routes: {}".format(routes))    



def vehicle_stop():
    global vehicleControlCommands
    global currentRouteDetailedSteps
    global current_steering
    global current_speed
    global current_leds
    global current_ldr
    global current_obstacle_distance

    vehicleControlCommands = []
    currentRouteDetailedSteps = []
    current_steering = 90.0
    current_speed = 0
    current_leds = [{"Color": "White", "Intensity": 0.0, "Blinking": "False"},
                            {"Color": "White", "Intensity": 0.0, "Blinking": "False"},
                            {"Color": "Red", "Intensity": 0.0, "Blinking": "False"},
                            {"Color": "Red", "Intensity": 0.0, "Blinking": "False"}]
    current_ldr = 0.0
    current_obstacle_distance = 0.0


def distance(p1, p2):
    p1Latitude = p1["latitude"]
    p1Longitude = p1["longitude"]
    p2Latitude = p2["latitude"]
    p2Longitude = p2["longitude"]
    # print("Calculando la distancia entre ({},{}) y ({},{})".format(p1["latitude"], p1["longitude"], p2["latitude"], p2["longitude"]))
    earth_radius = {"km": 6371.0087714, "mile": 3959}
    result = earth_radius["km"] * acos(cos((radians(p1Latitude))) * cos(radians(p2Latitude)) * cos(radians(p2Longitude) - radians(p1Longitude)) + sin(radians(p1Latitude)) * sin(radians(p2Latitude)))
    # print ("La distancia calculada es:{}".format(result))
    return result

def decode_polyline(polyline_str):
    """
    Pass a Google Maps encoded polyline string; returns list of lat/lon pairs
    """
    index, lat, lng = 0, 0, 0
    coordinates = []
    changes = {'latitude': 0, 'longitude': 0}
    # Coordinates have variable length when encoded, so just keep
    # track of whether we've hit the end of the string. In each
    # while loop iteration, a single coordinate is decoded.
    while index < len(polyline_str):
    # Gather lat/lon changes, store them in a dictionary to apply them later
        for unit in ['latitude', 'longitude']:
            shift, result = 0, 0
            while True:
                byte = ord(polyline_str[index]) - 63
                index += 1
                result |= (byte & 0x1f) << shift
                shift += 5
                if not byte >= 0x20:
                    break
            if (result & 1):
                changes[unit] = ~(result >> 1)
            else:
                changes[unit] = (result >> 1)

        lat += changes['latitude']
        lng += changes['longitude']
        coordinates.append((lat / 100000.0, lng / 100000.0))
    return coordinates
    
    ########################
    #    env simultation   #
    ########################

def obstacle_simulation():
    global current_obstacle_distance
    #print("Simulating distance to obstacles\n")
    if current_obstacle_distance > 0.0:
        current_obstacle_distance += random.uniform(-5.0, 5.0)
        if current_obstacle_distance < 0.0:
            current_obstacle_distance = 0.0
    else:
        current_obstacle_distance = random.uniform(0.0, 50.0)
    print(f"Obstacle distance: {current_obstacle_distance}\n")

def ldr_simulation():
    #print("Simulating LDR\n")
    global current_ldr
    if current_ldr > 0.0:
        current_ldr += random.uniform(-300.0, 300.0)
        if current_ldr < 0.0:
            current_ldr = 0.0
    else:
        current_ldr = random.uniform(0.0, 3000.0)
    print(f"Current luminosity: {current_ldr}\n")

def environment_simulator():
    print("Executing environment simulator thread\n")
    while True:
        obstacle_simulation()
        ldr_simulation()
        time.sleep(8)

def led_controller():
    """
    Function for execute vehicle leds
    :return:
    """
    print("Executing led controller thread\n")
    global current_leds
    try:
        while True:
            if current_steering > 100.0:
                print("Activate right signal lights\n")
                current_leds_str = (
                    '[{"Color": "White", "Intensity": 0.0, "Blinking": "False"},'
                    '{"Color": "Yellow", "Intensity": 100.0, "Blinking": "True"},'
                    '{"Color": "Red", "Intensity": 0.0, "Blinking": "False"},'
                    '{"Color": "Yellow", "Intensity": 100.0, "Blinking": "True"}]'
                )
                current_leds = json.loads(current_leds_str)

            elif current_steering < 80.0:
                print("Activate left signal lights\n")
                current_leds_str = (
                    '[{"Color": "Yellow", "Intensity": 100.0, "Blinking": "True"},'
                    '{"Color": "White", "Intensity": 0.0, "Blinking": "False"},'
                    '{"Color": "Yellow", "Intensity": 100.0, "Blinking": "True"},'
                    '{"Color": "Red", "Intensity": 0.0, "Blinking": "False"}]'
                )
                current_leds = json.loads(current_leds_str)

            elif current_braking and current_ldr > 1500:
                print("Activate brake lights at 50% intensity\n")
                current_leds_str = (
                    '[{"Color": "White", "Intensity": 0.0, "Blinking": "False"},'
                    '{"Color": "White", "Intensity": 0.0, "Blinking": "False"},'
                    '{"Color": "Red", "Intensity": 50.0, "Blinking": "False"},'
                    '{"Color": "Red", "Intensity": 50.0, "Blinking": "False"}]'
                )
                current_leds = json.loads(current_leds_str)

            elif current_braking and current_ldr <= 1500:
                print("Activate brake lights at 100% intensity\n")
                current_leds_str = (
                    '[{"Color": "White", "Intensity": 100.0, "Blinking": "False"},'
                    '{"Color": "White", "Intensity": 100.0, "Blinking": "False"},'
                    '{"Color": "Red", "Intensity": 100.0, "Blinking": "False"},'
                    '{"Color": "Red", "Intensity": 100.0, "Blinking": "False"}]'
                )
                current_leds = json.loads(current_leds_str)

            elif current_ldr > 1500:
                print("Deactivate low beam lights\n")
                current_leds_str = (
                    '[{"Color": "White", "Intensity": 0.0, "Blinking": "False"},'
                    '{"Color": "White", "Intensity": 0.0, "Blinking": "False"},'
                    '{"Color": "Red", "Intensity": 0.0, "Blinking": "False"},'
                    '{"Color": "Red", "Intensity": 0.0, "Blinking": "False"}]'
                )
                current_leds = json.loads(current_leds_str)

            elif current_ldr <= 1500:
                print("Activate low beam lights\n")
                current_leds_str = (
                    '[{"Color": "White", "Intensity": 100.0, "Blinking": "False"},'
                    '{"Color": "White", "Intensity": 100.0, "Blinking": "False"},'
                    '{"Color": "Red", "Intensity": 50.0, "Blinking": "False"},'
                    '{"Color": "Red", "Intensity": 50.0, "Blinking": "False"}]'
                )
                current_leds = json.loads(current_leds_str)
            #print(f"Current leds: "{current_leds}")
            print(f"Current leds: omitted for brevity")
            time.sleep(5)
    except KeyboardInterrupt:
        exit(0)


#######################
# MQTT Communications #
#######################


def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    if rc == 0:
        # Solicitar placa al conectarse
        client.subscribe(CONFIG_TOPIC)
        print(f"Subscribed to {CONFIG_TOPIC}")
        client.subscribe(ROUTES_TOPIC)
        client.publish(PLATE_REQUEST_TOPIC, payload=get_host_name(), qos=1, retain=False)
        print(f"Published to {PLATE_REQUEST_TOPIC}")
        # Suscribirse al tópico CONFIG_TOPIC para recibir la configuración/matricula

def on_message(client, userdata, msg):
    global vehicle_plate
    print(f"Message received: {msg.payload.decode()} on topic {msg.topic}")
    topic = msg.topic.split('/')
    if topic[-1] == "config":
        config_received = json.loads(msg.payload.decode())
        if config_received["plate"] != "Not Available":
            vehicle_plate = config_received["plate"]
            print(f"Vehicle plate updated to: {vehicle_plate}")

    elif topic[-1] == "routes":
        print("\n\n ====Routes received===========")
        global routes
        routes_received = json.loads(msg.payload.decode())
        if routes_received["origin"] != "" and routes_received["destination"] != "":
            routes.append(routes_received)
            print(f"Routes updated to: {routes}\n\n")

def getVehicleStatus():
    # Esta función debe retornar el estado actual del vehículo
    # Debes completar esta función basado en tus necesidades específicas
    return {
        "id": get_host_name(),
        "vehicle_plate": vehicle_plate,
        "current_position": current_position,
        "current_speed": current_speed,
        "current_steering": current_steering,
        "current_braking": current_braking,
        "current_leds": current_leds,
        "current_ldr": current_ldr,
        "current_obstacle_distance": current_obstacle_distance
        }


def publish_telemetry(client):
    # Aquí debes definir cómo se obtiene el estado actual del vehículo
    # Asumiré que existe una función getVehicleStatus() que hace esto
    vehicle_status = getVehicleStatus()  # Esta función necesita ser definida en otra parte de tu script
    json_telemetry = json.dumps(vehicle_status)
    client.publish(STATE_TOPIC + "/telemetry", payload=json_telemetry, qos=1)


def publish_event(client):
    payload_msg = {
        "plate": vehicle_plate,
        "event": "Route completed",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    payload_str = json.dumps(payload_msg)
    
    # send message to the server through mqtt that the route has been completed and the vehicle is ready for a new route
    client.publish(STATE_TOPIC + "/route_completed", payload=payload_str, qos=1, retain=False)
    print(f"Event message published: {payload_str}\n")



def mqtt_communications():
    global event_message
    global client


    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)

    client.username_pw_set(username="fic_server", password="fic_password")
    
    client.on_connect = on_connect
    client.on_message = on_message
    
    connection_dict = {
                    "id": get_host_name(),
                    "status": "Off - Unregular Diconnection",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
    
    connection_str = json.dumps(connection_dict)
    client.will_set(STATE_TOPIC + "/disconnect", payload=connection_str)


    MQTT_SERVER = os.getenv("MQTT_SERVER_ADDRESS")
    MQTT_PORT = int(os.getenv("MQTT_SERVER_PORT"))
    client.connect(MQTT_SERVER, MQTT_PORT, 60)
    client.loop_start()
    while True:
        if event_message != "":
            publish_event(client) # de momento solo hace cada 10 segundos, se puede mover a vehicle controller 
            event_message = ""
        publish_telemetry(client)
        time.sleep(15)
    client.loop_stop()


if __name__ == "__main__":
    try:

            mqtt_thread = threading.Thread(target=mqtt_communications, daemon=True)
            mqtt_thread.start()
            
            vehicle_thread = threading.Thread(target=vehicle_controller, daemon=True)
            vehicle_thread.start()

            environment_thread = threading.Thread(target=environment_simulator, daemon=True)
            environment_thread.start()

            led_thread = threading.Thread(target=led_controller, daemon=True)
            led_thread.start()

            print("Threads started\n")
            vehicle_thread.join()
            environment_thread.join()
            led_thread.join()
            mqtt_thread.join()

    except KeyboardInterrupt as exc:
        print(f"Exception: {exc}\n")
        vehicle_stop()
        exit(0)
