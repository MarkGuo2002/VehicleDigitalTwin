from flask import Flask, request
from flask_cors import CORS
from telemetry_db_manager import *
import os

app = Flask(__name__)
CORS(app)



@app.route('/telemetry/register/', methods=['POST'])
def register_telemetry():
    """Registers a new telemetry in the database and returns the plate assigned to it
    the data is processed by 'register_new_telemetry()'"""
    data = request.get_json()
    if register_new_telemetry(data):
        return {"result": "Telemetry registered"}, 201
    else:
        return {"result": "Error registering telemetry"}, 500


@app.route('/telemetry/vehicle/detailed_info/', methods=['GET'])
def retrieve_vehicle_detailed_info():
    """returns a list containing json of the last telemtries of the given vehicle_id
    the data is processed by 'get_vehicle_detailed_info()'"""
    data = request.get_json()
    vehicle_id = data['id']
    vehicle_info = get_vehicle_detailed_info(vehicle_id)
    if vehicle_info:
        return vehicle_info
    return ""


@app.route('/telemetry/vehicle/positions/', methods=['GET'])
def retrieve_vehicle_positions():
    """For each vehicle with status = 1, retuns a list like:
    return = [
    {
    "plate": plate,
    "latitud": latitud,
    "longitud": longitud
    },
    {...}
    ]
    Latitud y longitud are the last values of the vehicle_id"""
    return get_vehicles_last_positions()

if __name__ == '__main__':
    #should be run at 0.0.0.0:5002
    HOST = os.getenv('HOST')
    PORT = os.getenv('PORT')
    app.run(host=HOST, port=PORT)
