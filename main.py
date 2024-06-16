#!/usr/bin/env pybricks-micropython
from pybricks.hubs import EV3Brick
from pybricks.ev3devices import Motor, UltrasonicSensor
from pybricks.parameters import Port, Stop
from pybricks.robotics import DriveBase
import json
import socket
import time

SERVER_IP = '172.20.10.4'  # Opdateret IP-adresse hvis nødvendigt
SERVER_PORT = 5000

# Initialiser EV3-brick og sensorer
ev3 = EV3Brick()
left_wheel = Motor(Port.A)
right_wheel = Motor(Port.B)
front_arm = Motor(Port.C)
ultrasonic_sensor = UltrasonicSensor(Port.S1)
robot = DriveBase(left_wheel, right_wheel, wheel_diameter=65, axle_track=230)

def process_detections(detections):
    orange_balls = [d for d in detections if d['class'] == 'orange ball']

    if orange_balls:
        ev3.speaker.say("Jeg kan se en orange bold")
        move_towards_object(orange_balls[0]['center'])
        front_arm.run_angle(500, 360, Stop.HOLD)
    else:
        ev3.speaker.say("Jeg kan ikke se noget")

def move_towards_object(object_center, image_center=(320, 240)):
    x, y = object_center
    center_x, center_y = image_center
    if x < center_x:
        robot.turn(-10)
    elif x > center_x:
        robot.turn(10)
    robot.straight(50)

# Hovedloop
while True:
    try:
        # Opret en socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)

        # Forbind til serveren
        sock.connect((SERVER_IP, SERVER_PORT))
        
        # Send en HTTP GET-anmodning til serveren
        request = "GET /detect HTTP/1.1\r\nHost: {SERVER_IP}\r\n\r\n"
        sock.send(request.encode())
        
        # Modtag svaret fra serveren
        response = ""
        while True:
            data = sock.recv(1024)
            if not data:
                break
            response += data.decode()
        
        header, _, body = response.partition("\r\n\r\n")
        if body:
            try:
                result = json.loads(body)
                objects_detected = result['predictions']
                
                # Behandle detektionsresultater
                process_detections(objects_detected)
            except ValueError as e:
                print("Failed to decode JSON from body: {body}, Error: {e}")
        else:
            print("No body in response or body is empty.")
        
        # Luk socket-forbindelsen
        sock.close()

        # Tilføj en forsinkelse for at undgå spam
        time.sleep(1)

    except Exception as e:
        print("An error occurred: {e}")
        time.sleep(1)
