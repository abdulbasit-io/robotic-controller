import os
import random
import pygame  # Library to play sounds
import torch
import cv2
import time
import threading
from picamera2 import Picamera2
import RPi.GPIO as GPIO

# GPIO pin setup
X_STEP_PIN = 20
X_DIR_PIN = 21
Y_STEP_PIN = 27
Y_DIR_PIN = 23
LASER_PIN = 22

GPIO.setmode(GPIO.BCM)
GPIO.setup([X_STEP_PIN, X_DIR_PIN, Y_STEP_PIN, Y_DIR_PIN, LASER_PIN], GPIO.OUT)
GPIO.output(LASER_PIN, GPIO.LOW)  # Initialize laser OFF

# Load the YOLOv5 model
model = torch.hub.load('ultralytics/yolov5', 'custom', path='best.pt')  # replace 'best.pt' with your model path

# Initialize Picamera2
picam2 = Picamera2()
picam2.preview_configuration.main.size = (640, 480)  # Set resolution
picam2.preview_configuration.main.format = "RGB888"  # Format
picam2.preview_configuration.align()
picam2.configure("preview")
picam2.start()

# Sound folders
DISTRESS_CALL_FOLDER = "/home/user/Distress call"  # Replace with the actual path
PREDATOR_CALL_FOLDER = "/home/user/predator call"  # Replace with the actual path

# Initialize pygame mixer
pygame.mixer.init()

# Global variables
bird_detected = False
successful_detections = 0
system_paused = False
oscillation_active = False
bird_detection_active = False
threads = {}

# Global parameters adjustable via ControlCommand (with default values)
global_cycle_duration = 10      # e.g., seconds (or steps) for manual movement
global_cycle_rest = 120         # rest time between cycles
global_speaker_volume = 10      # (could be used to set volume)
global_speaker_duration = 8    # duration to play speaker sound
global_laser_duration = 10      # how long to activate laser in manual mode
global_laser_intensity = 60  

# Motor movement function with immediate stop check
def move_stepper(step_pin, dir_pin, steps, delay, direction):
    """MOve a stepper motot a given number of steps"""
    GPIO.output(dir_pin, GPIO.HIGH if direction == "forward" else GPIO.LOW)
    for _ in range(steps):
        if bird_detected or system_paused:
            print("Stopping stepper due to bird detection or system pause.")
            break
        GPIO.output(step_pin, GPIO.HIGH)
        time.sleep(delay)
        GPIO.output(step_pin, GPIO.LOW)
        time.sleep(delay)

# Oscillatory motion of the arm
def oscillate_steppers():
    global bird_detected, system_paused
    while True:
        if not bird_detected and not system_paused:
            print("No bird detected. Oscillating...")
            # Move Y-axis first
            move_stepper(X_STEP_PIN, X_DIR_PIN, steps=2000, delay=0.005, direction="forward")
            move_stepper(Y_STEP_PIN, Y_DIR_PIN, steps=2000, delay=0.005, direction="forward")
            move_stepper(Y_STEP_PIN, Y_DIR_PIN, steps=2000, delay=0.005, direction="backward")

            # Then move X-axis
            move_stepper(X_STEP_PIN, X_DIR_PIN, steps=2000, delay=0.005, direction="backward")
            move_stepper(Y_STEP_PIN, Y_DIR_PIN, steps=2000, delay=0.005, direction="forward")
            move_stepper(Y_STEP_PIN, Y_DIR_PIN, steps=2000, delay=0.005, direction="backward")
        elif system_paused:
            print("System paused. Oscillation stopped.")
        time.sleep(0.1)

def start_oscillation():
    """start oscillation thread if not already running"""
    global threads
    if "oscillation" not in threads or not threads["oscillation"].is_alive():
        threads["oscillation"] = threading.Thread(target=oscillate_steppers, daemon=True)
        threads["oscillation"].start()
        return "Oscillation started."
    return "Oscillation already running."

def stop_oscillation():
    """Stops the oscillation loop."""
    global oscillation_active
    oscillation_active = False
    return "Oscillation stopped."
  
# Sound deterrence function
def play_sound(folder, duration=None):
    """
    Plays a random sound from the specified folder for 8 seconds only.
    """
    try:
        files = [f for f in os.listdir(folder) if f.endswith((".mp3", ".wav"))]
        if not files:
            print(f"No sound files found in {folder}.")
            return

        selected_file = random.choice(files)
        file_path = os.path.join(folder, selected_file)
        print(f"Playing sound: {file_path}")

        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()

        # Play the sound for 8 seconds only
        start_time = time.time()
        while pygame.mixer.music.get_busy():
            if duration and (time.time() - start_time >= duration): 
                pygame.mixer.music.stop()
                break
            time.sleep(0.1)  # Allow other processes to run
        return f"Played sound: {selected_file}"

    except Exception as e:
        print(f"Error playing sound from {folder}: {e}")

# Bird detection function
def detect_birds():
    global bird_detected, successful_detections, system_paused, bird_detection_active
    bird_detection_active = True
    while bird_detection_active:
        if system_paused:
            print("System paused. Bird detection halted.")
            time.sleep(1)
            continue

        # Capture frame from Picamera2
        frame = picam2.capture_array()

        # Detect objects in the frame
        results = model(frame)
        labels, cords = results.xyxyn[0][:, -1], results.xyxyn[0][:, :-1]

        # Check if bird is detected (assuming label 0 corresponds to 'bird')
        if 0 in labels:
          bird_detected = True
          successful_detections += 1
          print(f"Bird detected! Activating deterrence. Detection count: {successful_detections}")
          GPIO.output(LASER_PIN, GPIO.HIGH)  # Activate laser briefly
          play_sound(DISTRESS_CALL_FOLDER, duration=global_speaker_duration)
          play_sound(PREDATOR_CALL_FOLDER, duration=global_speaker_duration)
          print("Deterrence complete. Resuming oscillation.")
          GPIO.output(LASER_PIN, GPIO.LOW)
          if successful_detections >= 3:
              system_paused = True
              print("Three successful detections reached. Pausing system for 5 minutes.")
              time.sleep(300)  # Pause system for 5 minutes
              successful_detections = 0
              system_paused = False
        else:
            bird_detected = False
            time.sleep(0.1)

    # Display the frame (optional)
    frame_with_boxes = plot_boxes((labels, cords), frame)
    cv2.imshow('YOLOv5 Detection', frame_with_boxes)

    # Break the loop on 'q' key press (optional for testing)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        return

# Function to plot bounding boxes (same as your code)
def plot_boxes(results, frame):
    labels, cords = results
    n = len(labels)
    for i in range(n):
        row = cords[i]
        if row[4] >= 0.4:  # Confidence threshold
            x1, y1, x2, y2 = int(row[0]*640), int(row[1]*480), int(row[2]*640), int(row[3]*480)
            bgr = (0, 255, 0)  # Bounding box color
            label = f'{model.names[int(labels[i])]} {row[4]:.2f}'  # Label with confidence
            cv2.rectangle(frame, (x1, y1), (x2, y2), bgr, 2)
            cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, bgr, 2)
    return frame


def start_bird_detection():
    """Starts the bird detection thread if not already running."""
    global threads
    if "detection" not in threads or not threads["detection"].is_alive():
        threads["detection"] = threading.Thread(target=detect_birds, daemon=True)
        threads["detection"].start()
        return "Bird detection started."
    return "Bird detection already running."

def stop_bird_detection():
    """Stops the bird detection loop."""
    global bird_detection_active
    bird_detection_active = False
    return "Bird detection stopped."
  

def update_parameters(command):
    """
    Update global parameters using values from the command.
    These parameters affect cycle duration, rest time, sound and laser durations, etc.
    """
    global global_cycle_duration, global_cycle_rest, global_speaker_volume, global_speaker_duration, global_laser_duration, global_laser_intensity
    if command.cycle_duration is not None:
        global_cycle_duration = command.cycle_duration
    if command.cycle_rest is not None:
        global_cycle_rest = command.cycle_rest
    if command.speaker_volume is not None:
        global_speaker_volume = command.speaker_volume
    if command.speaker_duration is not None:
        global_speaker_duration = command.speaker_duration
    if command.laser_duration is not None:
        global_laser_duration = command.laser_duration
    if command.laser_intensity is not None:
        global_laser_intensity = command.laser_intensity
    return "Parameters updated."
  
# remove this if you don't want it
def activate_laser(duration):
    """Activate laser for a specified duration."""
    GPIO.output(LASER_PIN, GPIO.HIGH)
    time.sleep(duration)
    GPIO.output(LASER_PIN, GPIO.LOW)

# remove this if you don't want it
def manual_control(command):
    """
    Handles manual control using the values provided from the webpage.
    Instead of stopping everything, it moves the robotic arm forward and backward dynamically.
    """
    print(f"Executing Manual Mode: {command}")

    steps = command.cycle_duration * 100  # Convert duration to step count
    delay = 0.005  # Step delay

    # Move forward
    move_stepper(X_STEP_PIN, X_DIR_PIN, steps, delay, "forward")
    move_stepper(Y_STEP_PIN, Y_DIR_PIN, steps, delay, "forward")

    # Rest for the specified cycle rest time
    time.sleep(command.cycle_rest)

    # Move backward
    move_stepper(Y_STEP_PIN, Y_DIR_PIN, steps, delay, "backward")
    move_stepper(X_STEP_PIN, X_DIR_PIN, steps, delay, "backward")

    # Activate laser if enabled
    if command.lasers:
        activate_laser(command.laser_duration)

    # Play sound if speakers are enabled
    if command.speakers:
        play_sound(DISTRESS_CALL_FOLDER, command.speaker_duration)

    return "Manual mode executed with forward and backward movement."


# Main function to control the arm
def control_arm(command):
    """
    Main function to control the robotic arm.
    Expects a parameter of type ControlCommand (which holds mode, timing, and control parameters).
    
    In 'automatic' mode:
      - Updates global parameters.
      - Starts oscillation and bird detection threads.
      
    In 'manual' mode:
      - Stops any automatic processes.
      - Performs manual control actions (e.g., moving the arm, activating laser, playing sound).
    """
    print("=== Control Command Received ===")
    print(f"Mode: {command.mode}")
    print(f"Start Time: {command.start_time}")
    print(f"End Time: {command.end_time}")
    print(f"Lasers: {command.lasers}")
    print(f"Speakers: {command.speakers}")
    print(f"Cycle Duration: {command.cycle_duration}")
    print(f"Cycle Rest: {command.cycle_rest}")
    print(f"Speaker Volume: {command.speaker_volume}")
    print(f"Speaker Duration: {command.speaker_duration}")
    print(f"Laser Duration: {command.laser_duration}")
    print(f"Laser Intensity: {command.laser_intensity}")
    
    # Update control parameters based on command
    print(update_parameters(command))
    
    # Decide action based on mode
    if command.mode.lower() == "automatic":
        osc_msg = start_oscillation()
        detect_msg = start_bird_detection()
        print(osc_msg, detect_msg)
        return "Automatic mode initiated."
    elif command.mode.lower() == "manual":
        manual_msg = manual_control(command)
        print(manual_msg)
        return "Manual mode executed."
    else:
        print("Unknown mode specified.")
        return "Unknown mode specified."



# --- For standalone testing ---
if __name__ == "__main__":
    # Create a dummy command object for testing.
    class DummyCommand:
        mode = "manual"           # Try "automatic" or "manual"
        start_time = "08:00"        # Not currently used in control logic, but available
        end_time = "18:00"
        lasers = True
        speakers = True
        cycle_duration = 10
        cycle_rest = 120
        speaker_volume = 10
        speaker_duration = 60
        laser_duration = 10
        laser_intensity = 60

    dummy = DummyCommand()
    result = control_arm(dummy)
    print("Result:", result)
    # Clean up GPIO and close windows when done (for testing purposes)
    GPIO.cleanup()
    cv2.destroyAllWindows()