from flask import Flask, request
from flask_cors import CORS
from vehicles_db_manager import *
import os

app = Flask(__name__)
CORS(app)



@app.route('/vehicles/register/', methods=['POST'])
def register_vehicle():
    # add a try catch block to handle the exception
    data = request.get_json()
    print(data)
    plate = register_new_vehicle(data)
    if plate != "":
        return {"plate": plate}, 201
    else:
        return {"plate": "Not Available"}, 400

@app.route('/vehicles/retrieve/', methods=['GET'])
def retrieve_vehicles():
    """retrieves a list in json with all the IDs and plates of all active vehicles in the database"""
    return retrieve_all_vehicles()

@app.route('/vehicles/toggle_status/', methods=['POST'])
def toggle():
    """toggles the status of a vehicle in the database, if the vehicle is active it will be deactivated and vice versa"""
    # add a try catch block to handle the exception
    data = request.get_json()
    print(data)
    return toggle_vehicle_status(data)
    
@app.route('/vehicles/debug/', methods=['GET'])
def vehicle_debug():
    """retrieves a list in json with all the IDs and plates of all active vehicles in the database"""
    return debug()

@app.route('/vehicles/delete/', methods=['POST'])
def delete_vehicle():
    """deletes a vehicle from the database"""
    # add a try catch block to handle the exception
    data = request.get_json()
    id = data["id"]
    return delete_vehicle_from_db(id)
    


if __name__ == '__main__':
    #should be run at 0.0.0.0:5001
    HOST = os.getenv('HOST')
    PORT = os.getenv('PORT')
    app.run(host=HOST, port=PORT)
