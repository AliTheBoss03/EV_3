import cv2
import socket
import numpy as np
import heapq
import time
import math
from ultralytics import YOLO

# Initialize the model
model = YOLO("/Users/alimo/Desktop/EV_3/AssetsBest/best_openvino_model")

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
camera_height = 170  # height of the camera from the field in cm (example value)
focal_length = 700  # focal length of the camera in pixels (example value)
robot_center = (100, 100)  # Initial assumption of the robot's center
robot_orientation = 0  # Initial orientation of the robot

# Define safe zone as a bounding box within 'walls'
def calculate_inner_safe_zone(obstacles, margin=50):  # Adjust margin for a smaller safe zone
    if not obstacles:
        return None
    x_coords = [pos[0] for pos in obstacles]
    y_coords = [pos[1] for pos in obstacles]
    x1, y1 = min(x_coords) + margin, min(y_coords) + margin
    x2, y2 = max(x_coords) - margin, max(y_coords) - margin
    return (x1, y1, x2, y2)

def calculate_distance(pixel_height):
    real_height_of_ball = 7  # cm (example value, adjust as necessary)
    distance = (real_height_of_ball * focal_length) / pixel_height
    return distance

def calculate_angle(target_pos, robot_center, robot_orientation):
    dx = target_pos[0] - robot_center[0]
    dy = target_pos[1] - robot_center[1]
    target_angle = np.arctan2(dy, dx) * (180 / np.pi)
    relative_angle = (target_angle - robot_orientation) % 360
    if relative_angle > 180:
        relative_angle -= 360
    return relative_angle

def is_within_safe_zone(pos, safe_zone):
    if safe_zone:
        x1, y1, x2, y2 = safe_zone
        return x1 <= pos[0] <= x2 and y1 <= pos[1] <= y2
    return False

def send_command(command, ip='172.20.10.10', port=5000):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_address = (ip, port)
    try:
        sock.sendto(command.encode(), server_address)
    finally:
        sock.close()

def astar(start, goal, obstacles, safe_zone):
    def heuristic(a, b):
        return np.linalg.norm(np.array(a) - np.array(b))

    def neighbors(node):
        x, y = node
        results = [(x+1, y), (x-1, y), (x, y+1), (x, y-1)]
        results = filter(lambda pos: 0 <= pos[0] < 640 and 0 <= pos[1] < 480, results)
        results = filter(lambda pos: pos not in obstacles and is_within_safe_zone(pos, safe_zone), results)
        return results

    queue = []
    heapq.heappush(queue, (0, start))
    came_from = {start: None}
    cost_so_far = {start: 0}

    while queue:
        _, current = heapq.heappop(queue)

        if current == goal:
            break

        for next in neighbors(current):
            new_cost = cost_so_far[current] + 1
            if next not in cost_so_far or new_cost < cost_so_far[next]:
                cost_so_far[next] = new_cost
                priority = new_cost + heuristic(goal, next)
                heapq.heappush(queue, (priority, next))
                came_from[next] = current

    # Check if a path was found
    if goal not in came_from:
        print(f"No path found to goal: {goal}")
        return []

    path = []
    node = goal
    while node:
        path.append(node)
        node = came_from[node]
    path.reverse()
    return path

# Open the video capture
cap = cv2.VideoCapture(0)

# Timer to trigger the robot to move to the target point every 2 minutes
start_time = time.time()
interval = 210  # Two minutes in seconds

while cap.isOpened():
    success, frame = cap.read()
    
    if success:
        # Perform inference
        results = model(frame, conf=0.4, imgsz=640)
        
        # Process results and determine command
        command = 'stop'  # Default command
        detections = results[0].boxes
        front_pos = None
        back_pos = None
        obstacles = []
        ball_positions = []
        big_goal_pos = None
        delay = 0.1  # Default delay

        for detection in detections:
            class_id = int(detection.cls[0])
            label = object_names.get(class_id, 'Unknown')
            x1, y1, x2, y2 = map(int, detection.xyxy[0])
            center_x, center_y = (x1 + x2) // 2, (y1 + y2) // 2
            if label == 'white ball':
                ball_positions.append((center_x, center_y))
            elif label == 'front':
                front_pos = (center_x, center_y)
            elif label == 'back':
                back_pos = (center_x, center_y)
            elif label in ['walls', 'cross']:
                obstacles.extend([(x1, y1), (x2, y2)])
            elif label == 'big goal':
                big_goal_pos = (center_x, center_y)

        if front_pos and back_pos:
            # Calculate the robot's center and orientation
            robot_center = ((front_pos[0] + back_pos[0]) // 2, (front_pos[1] + back_pos[1]) // 2)
            robot_orientation = np.arctan2(front_pos[1] - back_pos[1], front_pos[0] - back_pos[0]) * (180 / np.pi)
        else:
            robot_orientation = 0

        print(f"Robot center: {robot_center}, Orientation: {robot_orientation}")
        print(f"Detected balls: {ball_positions}")
        print(f"Detected obstacles: {obstacles}")

        # Calculate the inner safe zone
        safe_zone = calculate_inner_safe_zone(obstacles)

        # Filter balls within the safe zone
        ball_positions = [pos for pos in ball_positions if is_within_safe_zone(pos, safe_zone)]

        # Check if the robot is within the safe zone
        if not is_within_safe_zone(robot_center, safe_zone):
            print("Robot is out of the safe zone! Stopping...")
            send_command('move_backward')
            time.sleep(1)  # Adjust the time the robot moves backward
        
        elif ball_positions:
            # Use A* to find the path to the closest ball
            start = robot_center
            closest_ball = min(ball_positions, key=lambda pos: np.linalg.norm(np.array(pos) - np.array(start)))
            path = astar(start, closest_ball, obstacles, safe_zone)

            if not path:
                print(f"No valid path found to ball at {closest_ball}. Stopping...")
                command = 'stop'
            else:
                print(f"Path to the closest ball: {path}")

                if len(path) > 1:
                    next_move = path[1]  # The next move in the path
                    angle = calculate_angle(next_move, robot_center, robot_orientation)
                    print(f"Next move: {next_move}, Angle: {angle}")

                    # Tolerance angle for small adjustments
                    tolerance_angle = 15
                    
                    if -tolerance_angle <= angle <= tolerance_angle:
                        command = 'move_forward'
                    elif angle < -tolerance_angle:
                        command = 'turn_left'
                    elif angle > tolerance_angle:
                        command = 'turn_right'

                    # Calculate delay based on angle
                    delay = math.log1p(abs(angle)) * 0.1  # Adjust the multiplier as necessary

                    # Update robot center and orientation after command
                    if command == 'move_forward':
                        robot_center = next_move
                    elif command == 'turn_left':
                        robot_orientation -= 10  # Adjust based on actual turn angle
                    elif command == 'turn_right':
                        robot_orientation += 10  # Adjust based on actual turn angle
                else:
                    command = 'stop'
                    delay = 0.1  # Ensure delay is defined
        
        print(f"Sending command: {command}")

        # Send command to EV3
        send_command(command)

        # Add a delay to ensure the robot processes the command
        time.sleep(delay)  # Adjust the delay time as necessary
        
        # Plot and show the results
        annotated_frame = results[0].plot()

        # Draw the inner safe zone
        if safe_zone:
            x1, y1, x2, y2 = safe_zone
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (255, 0, 0), 2)  # Blue rectangle for inner safe zone
            
            # Draw point in the middle of the left line of the safe zone, aligned vertically with the center of big goal
            if big_goal_pos:
                point_x = x1  # Left boundary of the safe zone
                point_y = (y1 + y2) // 2  # Middle of the left boundary
                cv2.circle(annotated_frame, (point_x, point_y), 5, (0, 255, 0), -1)  # Green point

        cv2.imshow("Yolov8 Inference", annotated_frame)

        # Check if it's time to go to the target point and perform the actions
        current_time = time.time()
        if current_time - start_time >= interval:
            start_time = current_time
            # Move to the target point
            send_command('move_to_target_point')
            time.sleep(5)  # Allow time to move to the target point

            # Align the robot to the point
            send_command('align_to_target_point')
            time.sleep(2)  # Allow time to align

            # Perform the shooting sequence
            send_command('start_grabber_reverse')
            for _ in range(3):  # Repeat the forward and backward motion 3 times
                send_command('move_forward')
                time.sleep(1)  # Adjust based on needed motion duration
                send_command('move_backward')
                time.sleep(1)  # Adjust based on needed motion duration
            send_command('stop_grabber')

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
    else:
        # Break the loop if the end of the video is reached
        break

# Release the video capture object and close the display window
cap.release()
cv2.destroyAllWindows()
