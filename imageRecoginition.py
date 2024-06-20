from ultralytics import YOLO
import cv2
import socket
import numpy as np

# Initialize the model
model = YOLO("/Users/alimo/Desktop/EV_3/Assets/best_openvino_model")

# Define the object names based on the provided YAML
object_names = {
    0: 'back',
    1: 'big goal',
    2: 'cross',
    3: 'egg',
    4: 'front',
    5: 'orange ball',
    6: 'small goal',
    7: 'walls',
    8: 'white ball'
}

# Parameters for distance and angle calculation
camera_height = 300  # height of the camera from the field in cm (example value)
focal_length = 700  # focal length of the camera in pixels (example value)
robot_center = (320, 240)  # assume the robot is in the center of the frame

def calculate_distance(pixel_height):
    # Using a simple pinhole camera model to calculate distance
    real_height_of_ball = 7  # cm (example value, adjust as necessary)
    distance = (real_height_of_ball * focal_length) / pixel_height
    return distance

def calculate_angle(ball_position):
    dx = ball_position[0] - robot_center[0]
    dy = robot_center[1] - ball_position[1]  # assuming the origin is top-left
    angle = np.arctan2(dy, dx) * (180 / np.pi)
    return angle

def send_command(command, ip='172.20.10.2', port=5000):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_address = (ip, port)
    try:
        sock.sendto(command.encode(), server_address)
    finally:
        sock.close()

# Open the video capture
cap = cv2.VideoCapture(0)

while cap.isOpened():
    success, frame = cap.read()
    
    if success:
        # Perform inference
        results = model(frame, conf=0.4, imgsz=640)
        
        # Process results and determine command
        command = 'move_forward'  # Default command
        detections = results[0].boxes
        closest_ball = None
        min_distance = float('inf')
        
        for detection in detections:
            class_id = int(detection.cls[0])
            label = object_names.get(class_id, 'Unknown')
            if label == 'white ball':
                x1, y1, x2, y2 = map(int, detection.xyxy[0])
                ball_height = y2 - y1
                distance = calculate_distance(ball_height)
                if distance < min_distance:
                    min_distance = distance
                    closest_ball = ((x1 + x2) // 2, (y1 + y2) // 2)

        if closest_ball:
            angle = calculate_angle(closest_ball)
            if angle < -10:
                command = 'turn_left'
            elif angle > 10:
                command = 'turn_right'
            elif min_distance > 30:
                command = 'move_forward'
            else:
                command = 'grab'
        
        # Send command to EV3
        send_command(command)
        
        # Plot and show the results
        annotated_frame = results[0].plot()
        cv2.imshow("Yolov8 Inference", annotated_frame)
        
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
    else:
        # Break the loop if the end of the video is reached
        break

# Release the video capture object and close the display window
cap.release()
cv2.destroyAllWindows()
