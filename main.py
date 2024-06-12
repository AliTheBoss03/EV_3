#!/usr/bin/en
SERVER_IP = '172.20.10.4'  # Opdateret IP-adresse hvis nødvendigt
SERVER_PORT = 5000

# Funktion til at behandle detektionsresultater og handle derefter
def process_detections(detectv pybricks-micropython
from pybricks.hubs import EV3Brick
from pybricks.ev3devices import Motor, UltrasonicSensor
from pybricks.parameters import Port, Direction, Stop
from pybricks.robotics import DriveBase
import json
import socket
import time

# Initialiser EV3-brick og sensorer
ev3 = EV3Brick()

# Kontroller, at motorer og sensorer er korrekt tilsluttet
try:
    left_wheel = Motor(Port.A)
    right_wheel = Motor(Port.B)
    front_arm = Motor(Port.C)
    ultrasonic_sensor = UltrasonicSensor(Port.S1)
except OSError as e:
    ev3.speaker.beep()
    print("Fejl ved initialisering af enheder: ", e)
    raise

robot = DriveBase(left_wheel, right_wheel, wheel_diameter=65, axle_track=230)
ions):
    white_balls = [d for d in detections if d['class'] == 'white ball']
    orange_balls = [d for d in detections if d['class'] == 'orange ball']
    eggs = [d for d in detections if d['class'] == 'egg']
    walls = [d for d in detections if d['class'] == 'walls']
    crosses = [d for d in detections if d['class'] == 'cross']
    goal = [d for d in detections if d['class'] == 'big goal']

    if orange_balls:
        ev3.speaker.say("Orange ball detected")
        move_towards_object(orange_balls[0]['center'])
        front_arm.run_angle(500, 360, Stop.HOLD)  # Kør motoren for at fange bolden

    elif white_balls:
        ev3.speaker.say("White ball detected")
        move_towards_object(white_balls[0]['center'])
        front_arm.run_angle(500, 360, Stop.HOLD)  # Kør motoren for at fange bolden
    elif eggs or walls or crosses:
        ev3.speaker.say("Obstacle detected")
        robot.turn(180)  # Drej for at undgå forhindringen
    else:
        ev3.speaker.say("I have lost")

# Funktion til at bevæge sig mod et detekteret objekt
def move_towards_object(object_center, image_center=(320, 240)):
    x, y = object_center
    center_x, center_y = image_center
    if x < center_x:
        robot.turn(-10)  # Drej til venstre
    elif x > center_x:
        robot.turn(10)  # Drej til højre
    robot.straight(50)  # Kør fremad

# Hovedloop
while True:
    try:
        # Opret en socket
        print("Creating socket...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)  # Sæt en timeout for at undgå at hænge
        # Forbind til serveren
        print("Connecting to server at {}:{}...".format(SERVER_IP, SERVER_PORT))
        sock.connect((SERVER_IP, SERVER_PORT))
        
        # Send en HTTP GET-anmodning til serveren
        request = "GET /detect HTTP/1.1\r\nHost: {}\r\n\r\n".format(SERVER_IP)
        print("Sending request: {}".format(request))
        sock.send(request.encode())
        
        # Modtag svaret fra serveren
        response = ""
        while True:
            data = sock.recv(1024)
            if not data:
                break
            response += data.decode()
        
        print("Received response: {}".format(response))  # Tilføjet udskrivning af hele svaret
        
        header, _, body = response.partition("\r\n\r\n")
        if body:
            try:
                result = json.loads(body)
                objects_detected = result['predictions']
                
                # Behandle detektionsresultater
                process_detections(objects_detected)
            except ValueError:  # Fange JSON-dekodningsfejl
                print("Failed to decode JSON from body: {}".format(body))
        else:
            print("No body in response or body is empty.")
        
        # Luk socket-forbindelsen
        sock.close()

        # Tilføj en forsinkelse for at undgå spam
        time.sleep(1)

        # Opret en ny socket-forbindelse
        print("Creating socket...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)  # Sæt en timeout for at undgå at hænge
        
        # Forbind til serveren
        print("Connecting to server at {}:{}...".format(SERVER_IP, SERVER_PORT))
        sock.connect((SERVER_IP, SERVER_PORT))
        
        # Send en HTTP-anmodning til serveren
        request = "GET / HTTP/1.1\r\nHost: {}\r\n\r\n".format(SERVER_IP)
        print("Sending request: {}".format(request))
        sock.send(request.encode())
        
        response = ""
        while True:
            data = sock.recv(1024)
            if not data:
                break
            response += data.decode()
        
        print("Received response: {}".format(response))  # Tilføjet udskrivning af hele svaret
        
        header, _, body = response.partition("\r\n\r\n")
        if body:
            try:
                command = json.loads(body)  # Flyttet JSON-dekodning her
                print("Parsed JSON: {}".format(command))
                
                # Behandle kommandoer til robotten
                if 'wait' in command:
                    robot.stop()
                elif 'forward' in command:
                    dist = round(command['forward'])
                    robot.straight(dist)
                elif 'backward' in command:
                    robot.drive(-250, 0)
                elif 'left' in command:
                    robot.turn(command['left'])
                elif 'right' in command:
                    robot.turn(command['right'])
                elif 'onpoint' in command:
                    print("I'm at around angle 0, {}".format(round(command['onpoint'])))
                    dist = round(command['onpoint'])
                    robot.straight(dist)
                    left_arm = Motor(Port.C, Direction.COUNTERCLOCKWISE, [12, 36])
                    left_arm.control.limits(speed=150, acceleration=120)
                    left_arm.run(70)
                elif 'goal_point' in command:
                    print("I'm at point")
                    run = True
                    robot.straight(command['goal_point'])
                    robot.stop()
                    robot.drive(-100, 0)
                    time.sleep(2)
                    back_arm = Motor(Port.A, Direction.CLOCKWISE, [12, 36])
                    back_arm.control.limits(speed=60, acceleration=120)
                    back_arm.run(60)
                    robot.drive(250, 0)
                    time.sleep(2)
                    back_arm = Motor(Port.A, Direction.COUNTERCLOCKWISE, [12, 36])
                    back_arm.control.limits(speed=60, acceleration=120)
                    back_arm.run(60)
                elif 'forward_cross' in command:
                    robot.drive(280, 0)
                else:
                    print('Something went wrong: {}'.format(command['idk']))
            except ValueError:  # Fange JSON-dekodningsfejl
                print("Failed to decode JSON from body: {}".format(body))
        else:
            print("No body in response or body is empty.")
        
        # Luk socket-forbindelsen
        sock.close()
    except ValueError:  # Fange JSON-dekodningsfejl
        print("An error occurred: No JSON object could be decoded")
    except Exception as e:
        print("An error occurred: {}".format(e))

        # Tilføj en forsinkelse for at undgå spam
        time.sleep(1)
