import os
import mysql.connector
from datetime import datetime


def connect_database():
    mydb = mysql.connector.connect(
        host=os.getenv("DBHOST"),
        user=os.getenv("DBUSER"),
        password=os.getenv("DBPASSWORD"),
        database=os.getenv("DBDATABASE")
    )
    return mydb


def get_vehicle_id_by_plate(plate):
    mydb = connect_database()
    mycursor = mydb.cursor()
    query = "SELECT vehicle_id FROM vehicles WHERE plate = %s"
    mycursor.execute(query, (plate,))
    myresult = mycursor.fetchall()
    if len(myresult) > 0:
        return myresult[0][0]
    else:
        return None


def retrieve_vehicles():
    """This returns ALL the vehicles in the database, regardless of their status."""
    mydb = connect_database()
    mycursor = mydb.cursor()
    query = "SELECT plate FROM vehicles"
    mycursor.execute(query)
    myresult = mycursor.fetchall()
    plates = []
    for plate in myresult:
        data = {"plate": plate[0]}
        plates.append(data)
    return plates

def route_store_result(is_stored, db_instance, plate):
    print(f"Route store result:{is_stored}")
    mydb = db_instance

    if is_stored:
        query = "UPDATE vehicles SET status = 1 WHERE plate = %s;"
        with mydb.cursor() as cursor:
            cursor.execute(query, (plate,))
        mydb.commit()
        print(f"Storing result: Route insertion committed")
        return True
    else:
        print(f"Storing result: Route insertion rollback")
        mydb.rollback()
        return False


def assign_new_route(data):
    mydb = connect_database()
    print(f"Assigning route: {data}\n")

    with mydb.cursor() as cursor:
        sql = ("INSERT INTO routes (plate, origin, destination, time_stamp) VALUES (%s, %s, %s, %s);")

        tuple = (data["plate"], data["origin"], data["destination"], datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        try:
            cursor.execute(sql, tuple)
            print(f"Assign route: Inserted {cursor.rowcount} record of route\n")
            return True, mydb
        except Exception as exc:
            print(f"Assign route: Error inserting route. {exc}\n")
            return False, mydb


def get_routes_assigned_to_vehicle(plate):
    result = []
    mydb = connect_database()

    with mydb.cursor() as cursor:
        sql = ("""
            SELECT plate, origin, destination, time_stamp 
            FROM routes 
            WHERE plate = %s 
            ORDER BY time_stamp DESC LIMIT 20;
        """)
        try:
            cursor.execute(sql, (plate,))
            fetched_result = cursor.fetchall()
            for row in fetched_result:
                item = {
                    "plate": row[0],
                    "origin": row[1],
                    "destination": row[2],
                    "timestamp": row[3]
                }
                result.append(item)
            # set also the status of the vehicle to 1
            sql_update_status = "UPDATE vehicles SET status = 1 WHERE plate = %s;"
            cursor.execute(sql_update_status, (plate,))

            mydb.commit()
            print(f"Get vehicle routes: Got {cursor.rowcount} records of route\n")
            return result
        except Exception as exc:
            print(f"Get vehicle routes: Error getting vehicle´s routes. {exc}\n")
            error_result = {"Error Message": "Error getting vehicle's routes"}
            return error_result


def delete_route_db(plate, origin, destination):
    mydb = connect_database()

    sql = "DELETE FROM routes WHERE plate = %s AND origin = %s AND destination = %s;"
    with mydb.cursor() as cursor:
        try:
            cursor.execute(sql, (plate, origin, destination,))
            # set also the status of the vehicle to 0
            sql_update_status = "UPDATE vehicles SET status = 0 WHERE plate = %s;"
            cursor.execute(sql_update_status, (plate,))
            mydb.commit()
            print(f"Delete Route: {cursor.rowcount} record updated. Route form vehicle {plate} deleted\n")
            return True
        except Exception as exc:
            print(f"Delete Route: Error deleting route from vehicle {plate}")
            return False

def set_status_zero(plate):
    mydb = connect_database()
    sql = "UPDATE vehicles SET status = 0 WHERE plate = %s;"
    with mydb.cursor() as cursor:
        try:
            cursor.execute(sql, (plate,))
            mydb.commit()
            print(f"Set status zero: {cursor.rowcount} record updated. Status zero set for vehicle {plate}\n")
            return True
        except Exception as exc:
            print(f"Set status zero: Error setting status zero for vehicle {plate}\n")
            return False