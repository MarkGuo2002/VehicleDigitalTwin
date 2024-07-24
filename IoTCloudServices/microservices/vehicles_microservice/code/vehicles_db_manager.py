import mysql.connector as mysql
import os



def connect_database():
    mydb = mysql.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DBPASSWORD'),
        database=os.getenv('DBDATABASE')
    )
    return mydb

def delete_vehicle_from_db(id):
    mydb = connect_database()
    mycursor = mydb.cursor()
    try:
        #get the plate of the vehicle with the id
        query = "SELECT plate FROM vehicles WHERE vehicle_id = %s;"
        mycursor.execute(query, (id,))
        myresult = mycursor.fetchall()
        if len(myresult) == 0:
            return {"error": "Vehicle not found"}
        plate = myresult[0][0]
        #delete the vehicle from the database
        query = "DELETE FROM vehicles WHERE vehicle_id = %s;"
        mycursor.execute(query, (id,))
        mydb.commit()
        query = "UPDATE available_plates SET is_assigned = 0 WHERE plate = %s;"
        mycursor.execute(query, (plate,))
        mydb.commit()
    except Exception as e:
        return {"error": str(e)}
    return {"result": "Deleted"}
    

def retrieve_all_vehicles():
    mydb = connect_database()
    mycursor = mydb.cursor()
    query = "SELECT plate FROM vehicles where status = 1"
    mycursor.execute(query)
    myresult = mycursor.fetchall()
    plates = []
    for plate in myresult:
        data = {"plate": plate[0]}
        plates.append(data)
    return plates


def register_new_vehicle(data) -> str:
    """Registers a new vehicle in the database and returns the plate assigned to it"""
    mydb = connect_database()
    mycursor = mydb.cursor()

    # 1.- check if the vehicle is already registered, if it is return the plate
    query = "SELECT plate FROM vehicles WHERE vehicle_id = %s ORDER BY plate ASC LIMIT 1;"
    mycursor.execute(query, (data['vehicle_id'],))
    myresult = mycursor.fetchall()
    if len(myresult) > 0:
        return myresult[0][0]
    
    # 2.- get a available plate
    query = "SELECT plate, is_assigned FROM available_plates WHERE is_assigned = 0 ORDER BY plate ASC LIMIT 1;"
    mycursor.execute(query)
    myresult = mycursor.fetchall()
    if len(myresult) == 0:
        return ""
    plate = myresult[0][0]

    # 3.- assign the plate to the vehicle and insert into vehicles table
    query = "INSERT INTO vehicles (vehicle_id, plate) VALUES (%s, %s);"
    mycursor.execute(query, (data['vehicle_id'], plate))
    mydb.commit()
    
    # 4.- update the available plates table
    query = "UPDATE available_plates SET is_assigned = 1 WHERE plate = %s;"
    mycursor.execute(query, (plate,))
    mydb.commit()
    return plate
    
def debug():
    mydb = connect_database()
    mycursor = mydb.cursor()
    query = "SELECT * FROM vehicles; "
    mycursor.execute(query)
    myresult = mycursor.fetchall()
    vehicles = []
    for vehicle in myresult:
        data = {"id": vehicle[0], "vehicle_id": vehicle[1], "plate": vehicle[2], "status": vehicle[3]}
        vehicles.append(data)
    available_plates = []
    query = "SELECT * FROM available_plates;"
    mycursor.execute(query)
    myresult = mycursor.fetchall()
    for plate in myresult:
        data = {"plate": plate[1], "is_assigned": plate[2]}
        available_plates.append(data)
    routes = []
    query = "SELECT * FROM routes;"
    mycursor.execute(query)
    myresult = mycursor.fetchall()
    for route in myresult:
        data = {"origin": route[1], "destination": route[2], "plate": route[3], "timestamp": route[4]}
        routes.append(data)
    return {"vehicles": vehicles, "available_plates": available_plates, "routes": routes}


def toggle_vehicle_status(data):
    """Read the status of the vehicle according to the vehicle_id and toggle it and save it in the database and return the new status"""
    mydb = connect_database()
    mycursor = mydb.cursor()
    query = "SELECT status FROM vehicles WHERE vehicle_id = %s;"
    mycursor.execute(query, (data['vehicle_id'],))
    myresult = mycursor.fetchall()
    if len(myresult) == 0:
        return {"status": "Not Found"}
    status = myresult[0][0]
    if status == 1:
        status = 0
    else:
        status = 1
    query = "UPDATE vehicles SET status = %s WHERE vehicle_id = %s;"
    mycursor.execute(query, (status, data['vehicle_id']))
    mydb.commit()
    return {"status": status}