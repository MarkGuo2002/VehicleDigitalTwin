import os
import requests
from flask import Flask, request, json
from flask_cors import CORS
from routes_db_manager import *

app = Flask(__name__)
CORS(app)

def send_route_to_message_router(data):
    host = os.getenv("MESSAGE_ROUTER_ADDRESS")
    port = os.getenv("MESSAGE_ROUTER_PORT")
    result = requests.post("http://" + host + ":" + port + "/routes/send/", json=data)

    if result.status_code == 201:
        print(f"Route saved for vehicle {data['plate']}")
        return True
    else:
        print(f"Error saving route for vehicle {data['plate']}")
        return False

@app.route("/routes/assign/", methods=["POST"])
def routes_assign():
    """
    {
        "plate": "",
        "origin": "Navalcarnero",
        "destination": "Carranque"
    }
    """
    data = request.get_json()
    vehicle_id = get_vehicle_id_by_plate(data["plate"])
    if vehicle_id is None:
        return {"result": f"Vehicle {data['plate']} not found"}, 404
    # append the vehicle_id to the data dictionary
    data["vehicle_id"] = str(vehicle_id)
    vehicles = retrieve_vehicles()
    for v in vehicles:
        if data["plate"] == v["plate"]:
            result, db_instance = assign_new_route(data)
            if result:
                is_stored = send_route_to_message_router(data)
                if route_store_result(is_stored, db_instance, data["plate"]):
                    return {"result": "Route assigned"}, 201
    return {"result": f"Error assigning a new route to {data['plate']}"}, 500


@app.route("/routes/retrieve/", methods=["GET"])
def routes_retrieve():
    data = request.get_json()
    result = get_routes_assigned_to_vehicle(data["plate"])
    if isinstance(result, list):
        return result, 201
    else:
        return result, 500




@app.route("/routes/delete/", methods=["POST"])
def delete_route():
    """
    {
        "plate": "",
        "origin": "Navalcarnero",
        "destination": "Carranque"
    }
    """
    data = request.get_json()
    if delete_route_db(data["plate"], data["origin"], data["destination"]):
        print(f"Deleted route for vehicle {data['plate']} from {data['origin']} to {data['destination']}")
        return {"result": "Route deleted"}, 201
    else:
        print(f"Error deleting route for vehicle {data['plate']} from {data['origin']} to {data['destination']}")
        return {"result": "Error deleting route"}, 500

@app.route("/routes/status_zero/", methods=["POST"])
def status_zero():
    data = request.get_json()
    if set_status_zero(data["plate"]):
        print(f"Status zero set for vehicle {data['plate']}")
        return {"result": "Status zero set"}, 201
    else:
        print(f"Error setting status zero for vehicle {data['plate']}")
        return {"result": "Error setting status zero"}, 500

if __name__ == "__main__":
    HOST = os.getenv("HOST")
    PORT = os.getenv("PORT")
    app.run(host=HOST, port=PORT)
