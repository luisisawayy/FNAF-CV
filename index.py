"""
index.py - Combines the logic from binds_logic.py and webcam_gesture_demo.py into a single executable 
for user preference of running on a single machine as opposed to the distributed setup of running on two machines.

Usage:
    python index.py
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

# FNAF Game Configuration Coordinates
PAN_LEFT_X = 10
PAN_RIGHT_X = 1910
CENTER_X, CENTER_Y = 960, 600
L_DOOR = (68, 418)
L_LIGHT = (68, 563)
R_DOOR = (1520, 435)
R_LIGHT = (1520, 574)
TABLET = (700, 885)
MUTE_PHONE = (105, 35)
HONK_FREDDY = (848, 298)
PAN_DELAY = 0.4  

# Camera Navigation Maps
direction_index = {
    7: 0, # up
    8: 1, # down
    5: 2, # right
    3: 3, # left 
}

cam_direction_map = {
    "1A": ["0", "1B", "0", "0"],
    "1B": ["1A", "1C", "7", "5"],
    "1C": ["1B", "3", "7", "5"],
    "2A": ["1C", "2B", "4A", "3"],
    "2B": ["2A", "0", "4B", "0"],
    "3":  ["1C", "0", "2A", "0"],
    "4A": ["6", "4B", "6", "2A"],
    "4B": ["4A", "0", "0", "2B"],
    "5":  ["1B", "1C", "1B", "0"],
    "6":  ["7", "4A", "0", "4A"],
    "7":  ["1A", "6", "0", "1B"],
}

cam_pixel_map = {
    "1A": (1224, 435),
    "1B": (1200, 505),
    "1C": (1159, 604),
    "2A": (1223, 746),
    "2B": (1228, 799),
    "3":  (1119, 724),
    "4A": (1354, 748),
    "4B": (1359, 800),
    "5":  (1068, 544),
    "6":  (1483, 705),
    "7":  (1488, 536)
}

# State Variables
in_camera = False
curr_cam = "1A"
last_action_time = 0
COOLDOWN_SECONDS = 2.0

# FNAF Action Logic
def get_action_id(hand, gesture):
    """Maps hand and gesture combinations to specific action IDs for routing."""
    if gesture == "ok":
        return 1
    elif gesture == "palm" and hand == "Left":
        return 2
    elif gesture == "two_sideways_left":
        return 3
    elif gesture == "palm" and hand == "Right":
        return 4
    elif gesture == "two_sideways_right":
        return 5
    elif gesture == "mute":
        return 6
    elif gesture == "two_up":
        return 7
    elif gesture == "two_down":
        return 8
    return None

def camera_action(action_id):
    """Executes camera navigation actions based on the current camera and the action ID."""
    global in_camera, curr_cam
    if action_id == 1:
        print("Camera Action: Toggling Camera Tablet OFF")
        pyautogui.moveTo(TABLET[0], TABLET[1])
        pyautogui.moveTo(706, 765) 
        in_camera = False
    else:
        if action_id not in direction_index:
            return 
        dir_idx = direction_index[action_id]
        new_cam = cam_direction_map[curr_cam][dir_idx]
        if new_cam != "0":
            print(f"Camera Nav: {curr_cam} -> {new_cam}")
            curr_cam = new_cam
            target_x, target_y = cam_pixel_map[curr_cam]
            pyautogui.click(target_x, target_y)

def fnaf_action(action_id):
    """Executes the corresponding FNAF action through PyAutoGUI based on the action ID."""
    global in_camera
    if action_id == 1:
        print("Action 1: Toggling Camera Tablet ON")
        pyautogui.moveTo(TABLET[0], TABLET[1])
        pyautogui.moveTo(706, 765) 
        in_camera = True
    elif action_id == 2:
        print("Action 2: Toggling Left Door")
        pyautogui.moveTo(PAN_LEFT_X, CENTER_Y)
        time.sleep(PAN_DELAY)
        pyautogui.click(L_DOOR[0], L_DOOR[1])
    elif action_id == 3:
        print("Action 3: Flashing Left Light")
        pyautogui.moveTo(PAN_LEFT_X, CENTER_Y)
        time.sleep(PAN_DELAY)
        pyautogui.click(L_LIGHT[0], L_LIGHT[1])
        time.sleep(0.5)
        pyautogui.click(L_LIGHT[0], L_LIGHT[1]) 
    elif action_id == 4:
        print("Action 4: Toggling Right Door")
        pyautogui.moveTo(PAN_RIGHT_X, CENTER_Y)
        time.sleep(PAN_DELAY)
        pyautogui.click(R_DOOR[0], R_DOOR[1])
    elif action_id == 5:
        print("Action 5: Flashing Right Light")
        pyautogui.moveTo(PAN_RIGHT_X, CENTER_Y)
        time.sleep(PAN_DELAY)
        pyautogui.click(R_LIGHT[0], R_LIGHT[1])
        time.sleep(0.5) 
        pyautogui.click(R_LIGHT[0], R_LIGHT[1])
    elif action_id == 6:
        print("Action 6: Muting Phone Guy")
        pyautogui.click(MUTE_PHONE[0], MUTE_PHONE[1])
    elif action_id == 7:
        print("Action 7: Honk Freddy's Nose")
        pyautogui.moveTo(PAN_LEFT_X, CENTER_Y)
        time.sleep(PAN_DELAY)
        pyautogui.click(HONK_FREDDY[0], HONK_FREDDY[1]) 

def route_action(action_id):
    """Routes the incoming action to the correct function based on camera state."""
    if in_camera:
        camera_action(action_id)
    else:
        fnaf_action(action_id)

# Keyboard Bindings
for i in range(1, 9):
    keyboard.add_hotkey(str(i), lambda idx=i: route_action(idx))

# Computer Vision & Model Setup
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

# Inference Loop & Main Function
def main():
    global last_action_time
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model, idx_to_class = load_model(MODEL_PATH, device)

    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=2,
        min_detection_confidence=0.6,
        min_tracking_confidence=0.5,
    )

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
                    
                    # Action Executing Logic
                    action_id = get_action_id(hand_label, gesture_name)
                    if action_id is not None:
                        current_time = time.time()
                        if (current_time - last_action_time) > COOLDOWN_SECONDS:
                            print(f"GESTURE CLASSIFIED: {hand_label} Hand -> {gesture_name}")
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

        cv2.imshow("Hand Gesture Recognition (Background Feed)", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
    hands.close()

if __name__ == "__main__":
    main()