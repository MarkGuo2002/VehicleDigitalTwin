import requests
import os

host = os.getenv('VEHICLES_MICROSERVICE_ADDRESS')
port = os.getenv('VEHICLES_MICROSERVICE_PORT')
def register_vehicle(data):
    try:
        # http://34.28.186.251:5001/vehicles/debug/
        response = requests.post('http://' + host + ':' + port + '/vehicles/register/', json=data)
        if response.status_code == 201:
            # If the response status code is 201, the vehicle was registered successfully
            return response.json(), True
        else:
            # Handle other HTTP status codes and return the error message
            return response.json(), False
    except requests.exceptions.RequestException as e:
        # Handle errors during the request (e.g., network problems, invalid URL, etc.)
        return {'error': str(e)}, False

def delete_vehicle(data):
    response = requests.post("http://" + host + ":" + port + "/vehicles/delete/", json=data)
    if response.status_code == 200 or response.status_code == 201:
        return response.json()
    else:
        return {"Error": "Vehicle not found"}