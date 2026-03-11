"""
gesture_webcam.py - Real-time hand gesture recognition

Requirements:
    pip install torch torchvision mediapipe opencv-python

Usage:
    python gesture_webcam.py
"""

import cv2
import torch
import torch.nn as nn
import mediapipe as mp
import numpy as np
from torchvision import transforms, models
from pathlib import Path
import socket
import time

SCRIPT_DIR = Path(__file__).parent
MODEL_PATH = SCRIPT_DIR / "fnaf_hgr_final.pth"
CONFIDENCE_THRESHOLD = 0.55
CROP_PADDING = 0.25
IMG_SIZE = 224

# --- UDP CLIENT SETUP ---
UDP_IP = "100.83.49.246" # Computer 2's IPv4 Address goes here
UDP_PORT = 5005
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

last_send_time = 0
COOLDOWN_SECONDS = 3.0
TARGET_GESTURES = ["ok", "palm", "two_sideways_left", "two_sideways_right", "mute", "two_up"]
# ------------------------

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

    w = x_max - x_min
    h = y_max - y_min
    x_min = max(0, x_min - w * padding)
    y_min = max(0, y_min - h * padding)
    x_max = min(1, x_max + w * padding)
    y_max = min(1, y_max + h * padding)

    return (int(x_min * frame_w), int(y_min * frame_h),
            int(x_max * frame_w), int(y_max * frame_h))

def get_finger_direction(hand_landmarks):
    wrist = hand_landmarks.landmark[0]
    middle_tip = hand_landmarks.landmark[12]

    dx = middle_tip.x - wrist.x
    dy = middle_tip.y - wrist.y  

    if abs(dy) > abs(dx):
        return "up" if dy < 0 else "down"
    else:
        return "right" if dx > 0 else "left"

def main():
    global last_send_time
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")

    model, idx_to_class = load_model(MODEL_PATH, device)
    print(f"Classes: {list(idx_to_class.values())}")

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

    print("Press 'q' to quit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        h, w = frame.shape[:2]
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb)

        if results.multi_hand_landmarks:
            for hand_lm in results.multi_hand_landmarks:
                x1, y1, x2, y2 = get_hand_bbox(hand_lm, w, h)
                if x2 - x1 < 10 or y2 - y1 < 10:
                    continue

                crop_rgb = rgb[y1:y2, x1:x2]
                if crop_rgb.size == 0:
                    continue

                inp = preprocess(crop_rgb).unsqueeze(0).to(device)
                with torch.no_grad():
                    probs = torch.softmax(model(inp), dim=1)
                    conf, pred = probs.max(1)
                    conf = conf.item()
                    pred = pred.item()

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
                    
                    # --- UDP SEND LOGIC ---
                    if gesture_name in TARGET_GESTURES:
                        current_time = time.time()
                        if (current_time - last_send_time) > COOLDOWN_SECONDS:
                            # Package the hand and gesture together (e.g., "Left:palm")
                            payload = f"{hand_label}:{gesture_name}"
                            sock.sendto(payload.encode('utf-8'), (UDP_IP, UDP_PORT))
                            print(f"Network Send -> {payload}")
                            last_send_time = current_time
                    # ----------------------
                    
                else:
                    label = f"? ({conf:.0%})"
                    color = (128, 128, 128)

                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)
                cv2.rectangle(frame, (x1, y1 - th - 10), (x1 + tw, y1), color, -1)
                cv2.putText(frame, label, (x1, y1 - 5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)

                cv2.putText(frame, f"{hand_label} hand", (x1, y2 + 25),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 200, 0), 2)

        cv2.imshow("Hand Gesture Recognition", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
    hands.close()

if __name__ == "__main__":
    main()