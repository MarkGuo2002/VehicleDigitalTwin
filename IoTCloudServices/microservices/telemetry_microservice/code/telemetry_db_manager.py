import mysql.connector as mysql
import os
import datetime


def connect_database():
    mydb = mysql.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DBPASSWORD'),
        database=os.getenv('DBDATABASE')
    )
    return mydb


def register_new_telemetry(data):
    """Registers a new telemetry in the database and returns the plate assigned to it"""
    mydb = connect_database()
    mycursor = mydb.cursor()
    # Convert 'Blinking' from string to int (1 for True, 0 for False)
    for led in data["current_leds"]:
        led["Blinking"] = 1 if led["Blinking"] == "True" else 0
        led["Intensity"] = int(round(led["Intensity"]))

    current_time = datetime.datetime.now()
    formatted_time = current_time.strftime('%Y-%m-%d %H:%M:%S')

    query = """
        INSERT INTO vehicles_telemetry (
            vehicle_id,
            current_steering,
            current_speed,
            latitude,
            longitude,
            current_ldr,
            current_obstacle_distance,
            front_left_led_intensity,
            front_right_led_intensity,
            rear_left_led_intensity,
            rear_right_led_intensity,
            front_left_led_color,
            front_right_led_color,
            rear_left_led_color,
            rear_right_led_color,
            front_left_led_blinking,
            front_right_led_blinking,
            rear_left_led_blinking,
            rear_right_led_blinking,
            time_stamp
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        );
"""
    mycursor.execute(query, (data['id'],
                             data['current_steering'],
                             data['current_speed'],
                             data["current_position"]['latitude'],
                             data["current_position"]['longitude'],
                             data['current_ldr'],
                             data['current_obstacle_distance'],
                             data["current_leds"][0]["Intensity"],
                             data["current_leds"][1]["Intensity"],
                             data["current_leds"][2]["Intensity"],
                             data["current_leds"][3]["Intensity"],
                             data["current_leds"][0]["Color"],
                             data["current_leds"][1]["Color"],
                             data["current_leds"][2]["Color"],
                             data["current_leds"][3]["Color"],
                             data["current_leds"][0]["Blinking"],
                             data["current_leds"][1]["Blinking"],
                             data["current_leds"][2]["Blinking"],
                             data["current_leds"][3]["Blinking"],
                             formatted_time))
    mydb.commit()
    # check if the telemetry was inserted succcesfully, if it was return True else False
    query = "SELECT * FROM vehicles_telemetry WHERE vehicle_id = %s AND time_stamp = %s;"
    mycursor.execute(query, (data['id'], formatted_time))
    myresult = mycursor.fetchall()
    if len(myresult) > 0:
        return True
    return False

    

def get_vehicle_detailed_info(vehicle_id):
    mydb = connect_database()
    mycursor = mydb.cursor()
    query = """SELECT vehicle_id, current_steering, current_speed, current_ldr,
            current_obstacle_distance, front_left_led_intensity,
            front_right_led_intensity, rear_left_led_intensity,
            rear_right_led_intensity, front_left_led_color,
            front_right_led_color, rear_left_led_color, rear_right_led_color,
            front_left_led_blinking, front_right_led_blinking,
            rear_left_led_blinking, rear_right_led_blinking, time_stamp FROM
            vehicles_telemetry WHERE vehicle_id = %s ORDER BY time_stamp LIMIT 20;
            """
    mycursor.execute(query, (vehicle_id,))
    myresult = mycursor.fetchall()
    #check if result is empty
    if len(myresult) == 0:
        return ""
    
    vehicle_info = []
    for telemetry in myresult:
        data = {
            "vehicle_id": telemetry[0],
            "current_steering": telemetry[1],
            "current_speed": telemetry[2],
            "current_ldr": telemetry[3],
            "current_obstacle_distance": telemetry[4],
            "front_left_led_intensity": telemetry[5],
            "front_right_led_intensity": telemetry[6],
            "rear_left_led_intensity": telemetry[7],
            "rear_right_led_intensity": telemetry[8],
            "front_left_led_color": telemetry[9],
            "front_right_led_color": telemetry[10],
            "rear_left_led_color": telemetry[11],
            "rear_right_led_color": telemetry[12],
            "front_left_led_blinking": telemetry[13],
            "front_right_led_blinking": telemetry[14],
            "rear_left_led_blinking": telemetry[15],
            "rear_right_led_blinking": telemetry[16],
            "time_stamp": telemetry[17]
        }
        vehicle_info.append(data)
    return vehicle_info

    

def get_vehicles_last_positions():
    mydb = connect_database()
    mycursor = mydb.cursor(dictionary=True)  # Fetch the results as dictionaries
    query = """
        SELECT 
            v.vehicle_id,
            v.plate,
            vt.latitude,
            vt.longitude,
            vt.time_stamp
        FROM 
            vehicles v
        JOIN 
            vehicles_telemetry vt ON v.vehicle_id = vt.vehicle_id
        INNER JOIN (
            SELECT 
                vehicle_id, 
                MAX(time_stamp) AS max_time_stamp
            FROM 
                vehicles_telemetry
            GROUP BY 
                vehicle_id
        ) AS subvt ON vt.vehicle_id = subvt.vehicle_id AND vt.time_stamp = subvt.max_time_stamp
        WHERE 
            v.status = 1;
    """
    mycursor.execute(query)
    myresult = mycursor.fetchall()
    vehicles_positions = []
    for vehicle in myresult:
        data = {
            "vehicle_id": vehicle['vehicle_id'],
            "plate": vehicle['plate'],
            "latitude": vehicle['latitude'],
            "longitude": vehicle['longitude'],
            "time_stamp": vehicle['time_stamp'].strftime('%Y-%m-%d %H:%M:%S')  # Format the timestamp
        }
        vehicles_positions.append(data)
    mycursor.close()
    mydb.close()
    return vehicles_positions

