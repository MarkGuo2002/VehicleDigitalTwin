import requests
import os

host = os.getenv('TELEMETRY_MICROSERVICE_ADDRESS')
port = os.getenv('TELEMETRY_MICROSERVICE_PORT')

route_host = os.getenv('ROUTES_MICROSERVICE_ADDRESS')
route_port = os.getenv('ROUTES_MICROSERVICE_PORT')

def register_telemetry (data):
    try:
        response = requests.post('http://' + host + ':' + port + '/telemetry/register/', json=data)
        if response.status_code == 201:
            # If the response status code is 201, the vehicle was registered successfully
            return response.json(), True
        else:
            # Handle other HTTP status codes and return the error message
            return response.json(), False
    except requests.exceptions.RequestException as e:
        # Handle errors during the request (e.g., network problems, invalid URL, etc.)
        return {'error': str(e)}, False

def delete_route(data):
    result = requests.post("http://" + route_host + ":" + route_port + "/routes/delete/", json=data)
    if result.status_code == 201:
        return {"result": "Route deleted"}, 201
    else:
        return {"result": "Error deleting route"}, 500

def status_zero(data):
    route_host = os.getenv('ROUTES_MICROSERVICE_ADDRESS')
    route_port = os.getenv('ROUTES_MICROSERVICE_PORT')
    result = requests.post("http://" + route_host + ":" + route_port + "/routes/status_zero/", json=data)
    if result.status_code == 201:
        return {"result": "Status zero set"}, 201
    else:
        return {"result": "Error setting status zero"}, 500