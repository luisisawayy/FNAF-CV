"""
index2.py - Combines the logic from binds_fnaf2.py and webcam_gesture_demo.py into a single executable file
for user preference of running on a single machine as opposed to the distributed setup of running on two machines.

Usage:
    python index2.py
"""

import cv2
import torch
import torch.nn as nn
import mediapipe as mp
import numpy as np
from torchvision import transforms, models
from pathlib import Path
import time
import pyautogui
import keyboard
import threading

# FNAF 2 Configuration & Coordinates
PAN_LEFT_X = 10
PAN_RIGHT_X = 1910
CENTER_X, CENTER_Y = 960, 600

MUTE_PHONE = (429, 84)     # Mute Phone Button at Top Left of the Office
HONK_FREDDY = (284, 258)   # Freddy poster in the office
LEFT_VENT = (300, 668)     # Left Air Vent
RIGHT_VENT = (1620, 661)   # Right Air Vent
MASK_ZONE = (466, 1129)    # Bottom left hover zone
TABLET_ZONE = (1382, 1136) # Bottom right hover zone
MUSIC_BOX = (801, 927)     # Wind up music box button inside Cam 11

PAN_DELAY = 0.55  

# maps actions to camera directions: up (0), down (1), right (2), left (3)
direction_index = {
    6: 0, # up
    8: 1, # down
    4: 2, # right
    3: 3, # left 
}

# maps cameras to their directional neighbors (up, down, right, left)
cam_direction_map = {
    "1":  ["3", "5", "2", "0"],    
    "2":  ["4", "6", "10", "1"],   
    "3":  ["8", "1", "4", "0"],    
    "4":  ["7", "2", "10", "3"],   
    "5":  ["1", "0", "6", "0"],    
    "6":  ["2", "0", "0", "5"],    
    "7":  ["0", "4", "9", "8"],    
    "8":  ["0", "3", "7", "0"],    
    "9":  ["0", "11", "0", "7"],   
    "10": ["9", "12", "11", "4"],  
    "11": ["9", "12", "0", "10"],  
    "12": ["11", "0", "0", "10"]   
}

# pixel coordinates for the 12 camera buttons
cam_pixel_map = {
    "1": (1121, 876), 
    "2": (1372, 871), 
    "3": (1122, 764),
    "4": (1372, 763), 
    "5": (1142, 1017),  
    "6": (1353, 1008),
    "7": (1415, 668), 
    "8": (1122, 653),  
    "9": (1702, 606),
    "10": (1582, 790), 
    "11": (1775, 727), 
    "12": (1751, 868)
}

# State Variables
in_camera = False
mask_on = False
curr_cam = "9" # Starting on Cam 9 matches the game's default starting state
last_action_time = 0
COOLDOWN_SECONDS = 2.0

# Game Logic
def get_action_id(hand, gesture):
    """Maps hand and gesture combinations to specific action IDs for routing."""
    if gesture == "ok" and hand == "Right": return 1            # Toggle Tablet (Right ok)
    elif gesture == "palm" and hand == "Left": return 2         # Toggle Mask (Left palm)
    elif gesture == "two_sideways_left": return 3               # Check Left Vent (Any)
    elif gesture == "two_sideways_right": return 4              # Check Right Vent (Any)
    elif gesture == "palm" and hand == "Right": return 5        # Flashlight (Right palm)
    elif gesture == "two_up": return 6                          # Boop Freddy's Nose (Any)
    elif gesture == "ok" and hand == "Left": return 7           # Wind Music Box (Left ok)
    elif gesture == "two_down": return 8                        # Navigate Down (Camera Mode)
    return None

def camera_action(action_id):
    """Executes camera navigation actions based on the current camera and the action ID."""
    global in_camera, curr_cam
    
    if action_id == 1:
        print("Camera Action: Toggling Camera Tablet OFF")
        pyautogui.moveTo(TABLET_ZONE[0], TABLET_ZONE[1])
        pyautogui.moveTo(971, 1035)
        in_camera = False
        
    elif action_id == 5:
        print("Camera Action: Flashing Light in Camera (1s)")
        keyboard.press('ctrl')
        time.sleep(1.0)
        keyboard.release('ctrl')
        
    elif action_id == 7:
        print("Camera Action: Winding Music Box (5s Hold)")
        if curr_cam != "11":
            curr_cam = "11"
            target_x, target_y = cam_pixel_map[curr_cam]
            pyautogui.click(target_x, target_y)
            time.sleep(0.2) 
            
        pyautogui.moveTo(MUSIC_BOX[0], MUSIC_BOX[1])
        pyautogui.mouseDown()
        time.sleep(5.0)
        pyautogui.mouseUp()
        print("Music Box Wound.")
        
    else:
        if action_id not in direction_index:
            return 
        dir_idx = direction_index[action_id]
        if curr_cam in cam_direction_map:
            new_cam = cam_direction_map[curr_cam][dir_idx]
            if new_cam != "0":
                print(f"Camera Nav: Cam {curr_cam} -> Cam {new_cam}")
                curr_cam = new_cam
                target_x, target_y = cam_pixel_map[curr_cam]
                pyautogui.click(target_x, target_y)

def fnaf_action(action_id):
    """Executes the corresponding FNAF action through PyAutoGUI based on the action ID."""
    global in_camera, mask_on
    
    if action_id == 1 and not mask_on:
        print("Action 1: Toggling Camera Tablet ON")
        pyautogui.moveTo(TABLET_ZONE[0], TABLET_ZONE[1])
        pyautogui.moveTo(971, 1035)
        in_camera = True
        
    elif action_id == 2 and not in_camera:
        print(f"Action 2: Toggling Freddy Mask {'OFF' if mask_on else 'ON'}")
        pyautogui.moveTo(MASK_ZONE[0], MASK_ZONE[1])
        pyautogui.moveTo(971, 1035)
        mask_on = not mask_on
        
    elif action_id == 3 and not in_camera and not mask_on:
        print("Action 3: Checking Left Vent")
        pyautogui.moveTo(PAN_LEFT_X, CENTER_Y)
        time.sleep(PAN_DELAY)
        pyautogui.moveTo(LEFT_VENT[0], LEFT_VENT[1])
        pyautogui.mouseDown()
        time.sleep(0.5)
        pyautogui.mouseUp()
        
    elif action_id == 4 and not in_camera and not mask_on:
        print("Action 4: Checking Right Vent")
        pyautogui.moveTo(PAN_RIGHT_X, CENTER_Y)
        time.sleep(PAN_DELAY)
        pyautogui.moveTo(RIGHT_VENT[0], RIGHT_VENT[1])
        pyautogui.mouseDown()
        time.sleep(0.5)
        pyautogui.mouseUp()
        
    elif action_id == 5 and not in_camera and not mask_on:
        print("Action 5: Flashing Hallway Light (1s)")
        keyboard.press('ctrl')
        time.sleep(1.0)
        keyboard.release('ctrl')
        
    elif action_id == 6 and not in_camera and not mask_on:
        print("Action 6: Honk Freddy's Nose")
        pyautogui.moveTo(PAN_LEFT_X, CENTER_Y)
        time.sleep(PAN_DELAY)
        pyautogui.click(HONK_FREDDY[0], HONK_FREDDY[1])

    elif action_id == 9 and not in_camera and not mask_on:
        print("Action 9: Muting Phone Guy")
        pyautogui.click(MUTE_PHONE[0], MUTE_PHONE[1])

def route_action(action_id):
    if in_camera:
        camera_action(action_id)
    else:
        fnaf_action(action_id)

# Keyboard Bindings
for i in range(1, 9):
    keyboard.add_hotkey(str(i), lambda idx=i: route_action(idx))


# CV Model Setup
SCRIPT_DIR = Path(__file__).parent
MODEL_PATH = SCRIPT_DIR / "fnaf_hgr_final.pth"
CONFIDENCE_THRESHOLD = 0.55
CROP_PADDING = 0.25
IMG_SIZE = 224

preprocess = transforms.Compose([
    transforms.ToPILImage(),
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])

def load_model(path, device):
    ckpt = torch.load(path, map_location=device, weights_only=False)
    classes = ckpt["classes"]
    idx_to_class = {i: c for i, c in enumerate(classes)}
    model = models.resnet18(weights=None)
    model.fc = nn.Linear(model.fc.in_features, len(classes))
    model.load_state_dict(ckpt["state_dict"])
    model.to(device)
    model.eval()
    return model, idx_to_class

def get_hand_bbox(hand_landmarks, frame_w, frame_h, padding=CROP_PADDING):
    xs = [lm.x for lm in hand_landmarks.landmark]
    ys = [lm.y for lm in hand_landmarks.landmark]
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)
    w, h = x_max - x_min, y_max - y_min
    x_min = max(0, x_min - w * padding)
    y_min = max(0, y_min - h * padding)
    x_max = min(1, x_max + w * padding)
    y_max = min(1, y_max + h * padding)
    return (int(x_min * frame_w), int(y_min * frame_h), int(x_max * frame_w), int(y_max * frame_h))

def get_finger_direction(hand_landmarks):
    wrist, middle_tip = hand_landmarks.landmark[0], hand_landmarks.landmark[12]
    dx, dy = middle_tip.x - wrist.x, middle_tip.y - wrist.y  
    if abs(dy) > abs(dx): return "up" if dy < 0 else "down"
    else: return "right" if dx > 0 else "left"

# Main Loop
def main():
    global last_action_time
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Loading Model on {device}...")
    model, idx_to_class = load_model(MODEL_PATH, device)

    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(static_image_mode=False, max_num_hands=2, min_detection_confidence=0.6, min_tracking_confidence=0.5)

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    print("Press 'ESC' at any time to quit.")

    while True:
        if keyboard.is_pressed('esc'):
            break

        ret, frame = cap.read()
        if not ret: break

        frame = cv2.flip(frame, 1)
        h, w = frame.shape[:2]
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb)

        if results.multi_hand_landmarks:
            for hand_lm in results.multi_hand_landmarks:
                x1, y1, x2, y2 = get_hand_bbox(hand_lm, w, h)
                if x2 - x1 < 10 or y2 - y1 < 10: continue

                crop_rgb = rgb[y1:y2, x1:x2]
                if crop_rgb.size == 0: continue

                inp = preprocess(crop_rgb).unsqueeze(0).to(device)
                with torch.no_grad():
                    probs = torch.softmax(model(inp), dim=1)
                    conf, pred = probs.max(1)
                    conf, pred = conf.item(), pred.item()

                hand_label = "?"
                if results.multi_handedness:
                    hand_idx = list(results.multi_hand_landmarks).index(hand_lm)
                    handedness = results.multi_handedness[hand_idx].classification[0].label
                    hand_label = "Left" if handedness == "Left" else "Right"

                if conf >= CONFIDENCE_THRESHOLD:
                    gesture_name = idx_to_class[pred]
                    if gesture_name == "two_sideways":
                        direction = get_finger_direction(hand_lm)
                        if direction in ("left", "right"):
                            gesture_name = f"two_sideways_{direction}"

                    label = f"{gesture_name} ({conf:.0%})"
                    color = (0, 255, 0)
                    
                    # Execution Logic
                    action_id = get_action_id(hand_label, gesture_name)
                    if action_id is not None:
                        current_time = time.time()
                        if (current_time - last_action_time) > COOLDOWN_SECONDS:
                            print(f"[ACTION FIRED] {hand_label} Hand -> {gesture_name}")
                            threading.Thread(target=route_action, args=(action_id,)).start()
                            last_action_time = current_time
                else:
                    label = f"? ({conf:.0%})"
                    color = (128, 128, 128)

                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)
                cv2.rectangle(frame, (x1, y1 - th - 10), (x1 + tw, y1), color, -1)
                cv2.putText(frame, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
                cv2.putText(frame, f"{hand_label} hand", (x1, y2 + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 200, 0), 2)

        cv2.imshow("FNAF 2 Hand Gesture Recognition", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
    hands.close()

if __name__ == "__main__":
    main()