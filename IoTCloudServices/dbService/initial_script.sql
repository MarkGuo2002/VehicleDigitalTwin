-- create database
create database fic_data;

-- Create a new user (only with local access) and grant privileges to this user on the new database:
grant all privileges on fic_data.* TO 'fic_db_user'@'%' identified by '1234';

-- After modifying the MariaDB grant tables, execute the following command in order to apply the changes:
flush privileges;

-- Change to the created database
use fic_data;

-- create table for storing device IDs
CREATE TABLE available_plates (
 	id MEDIUMINT NOT NULL AUTO_INCREMENT,
 	plate varchar(7) NOT NULL,
 	is_assigned TINYINT,
 	UNIQUE (plate),
 	PRIMARY KEY (id)
 );

INSERT INTO available_plates (plate, is_assigned) VALUES ('0001BBB',0);
INSERT INTO available_plates (plate, is_assigned) VALUES ('0002BBB',0);
INSERT INTO available_plates (plate, is_assigned) VALUES ('0003BBB',0);
INSERT INTO available_plates (plate, is_assigned) VALUES ('0004BBB',0);
INSERT INTO available_plates (plate, is_assigned) VALUES ('0005BBB',0);
INSERT INTO available_plates (plate, is_assigned) VALUES ('0006BBB',0);
INSERT INTO available_plates (plate, is_assigned) VALUES ('0007BBB',0);
INSERT INTO available_plates (plate, is_assigned) VALUES ('0008BBB',0);
INSERT INTO available_plates (plate, is_assigned) VALUES ('0009BBB',0);
INSERT INTO available_plates (plate, is_assigned) VALUES ('0010BBB',0);

-- query over vehicles table
SELECT plate, is_assigned FROM available_plates ORDER BY plate DESC;

--  create table for storing vehicles identification information
CREATE TABLE vehicles (
 	id MEDIUMINT NOT NULL AUTO_INCREMENT,
 	vehicle_id varchar(50) NOT NULL,
 	plate varchar(7) NOT NULL,
    status TINYINT,
 	UNIQUE (vehicle_id, plate),
 	PRIMARY KEY (id)
 );

--  query over vehicles table
SELECT vehicle_id, plate, status FROM vehicles ORDER BY vehicle_id DESC;

--  create table for vehicles telemetry
CREATE TABLE vehicles_telemetry (
 	id MEDIUMINT NOT NULL AUTO_INCREMENT,
 	vehicle_id varchar(50) NOT NULL,
 	current_steering float NOT NULL,
 	current_speed float NOT NULL,
 	latitude float NOT NULL,
 	longitude float NOT NULL,
 	current_ldr float,
 	current_obstacle_distance float,
 	front_left_led_intensity int,
 	front_right_led_intensity int,
 	rear_left_led_intensity int,
 	rear_right_led_intensity int,
 	front_left_led_color varchar(10),
 	front_right_led_color varchar(10),
 	rear_left_led_color varchar(10),
 	rear_right_led_color varchar(10),
 	front_left_led_blinking TINYINT,
 	front_right_led_blinking TINYINT,
 	rear_left_led_blinking TINYINT,
 	rear_right_led_blinking TINYINT,
 	time_stamp timestamp NOT NULL,
 	PRIMARY KEY (id)
 );

-- query over table sensor_data
SELECT vehicle_id, current_steering, current_speed, latitude, longitude, current_ldr, current_obstacle_distance,
       front_left_led_intensity, front_right_led_intensity, rear_left_led_intensity, rear_right_led_intensity,
       front_left_led_color, front_right_led_color, rear_left_led_color, rear_right_led_color,
       front_left_led_blinking, front_right_led_blinking, rear_left_led_blinking, rear_right_led_blinking, time_stamp
FROM vehicles_telemetry ORDER BY vehicle_id DESC;


-- create table for storing vehicles identification information
CREATE TABLE routes (
 	id MEDIUMINT NOT NULL AUTO_INCREMENT,
 	origin varchar(100) NOT NULL,
 	destination varchar(100) NOT NULL,
 	plate varchar(7) NOT NULL,
 	time_stamp timestamp NOT NULL,
 	PRIMARY KEY (id)
 );

-- query over vehicles table
SELECT origin, destination, plate, time_stamp FROM routes ORDER BY time_stamp DESC;