"""
binds_fnaf2.py - Contains the logic for handling keyboard bindings and mapping them to FNAF 2 actions based
on inference results from the computer vision gesture model.

Usage:
    python binds_fnaf2.py
"""
import pyautogui
import time
import keyboard
import socket
import threading

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
    6: 0, # two_up
    8: 1, # two_down
    4: 2, # two_sideways_right
    3: 3, # two_sideways_left
}

# maps cameras to their directional neighbors (up, down, right, left)
cam_direction_map = {
    "1":  ["3", "5", "2", "0"],    # Party Room 1
    "2":  ["4", "6", "10", "1"],   # Party Room 2
    "3":  ["8", "1", "4", "0"],    # Party Room 3
    "4":  ["7", "2", "10", "3"],   # Party Room 4
    "5":  ["1", "0", "6", "0"],    # Left Air Vent
    "6":  ["2", "0", "0", "5"],    # Right Air Vent
    "7":  ["0", "4", "9", "8"],    # Main Hall
    "8":  ["0", "3", "7", "0"],    # Parts/Service
    "9":  ["0", "11", "0", "7"],   # Show Stage
    "10": ["9", "12", "11", "4"],  # Game Area
    "11": ["9", "12", "0", "10"],  # Prize Corner (Music Box)
    "12": ["11", "0", "0", "10"]   # Kid's Cove
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
curr_cam = "9" # Camera tablet starts at camera 9 by default

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
    elif gesture == "mute": return 9                            # Mute Phone (Any)
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
        time.sleep(0.5)
        keyboard.release('ctrl')
        
    elif action_id == 7:
        print("Camera Action: Winding Music Box (5s Hold)")
        # Navigate to Cam 11 automatically just in case they aren't there
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
        # Camera Navigation Logic (uses IDs 3, 4, 6, 8)
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
        print("Action 5: Flashing Hallway Light (0.5s)")
        keyboard.press('ctrl')
        time.sleep(0.5)
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
    """Routes the incoming action to the correct function based on camera state."""
    if in_camera:
        camera_action(action_id)
    else:
        fnaf_action(action_id)

def start_udp_server():
    """Listens for incoming network gestures and parses handedness."""
    UDP_IP = "0.0.0.0" 
    UDP_PORT = 5005
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))
    
    print(f"\n[NETWORK] FNAF 2 Server actively listening on port {UDP_PORT}...")
    
    while True:
        data, addr = sock.recvfrom(1024) 
        payload = data.decode('utf-8')
        
        if ":" in payload:
            hand, gesture = payload.split(":", 1)
            action_id = get_action_id(hand, gesture)
            
            if action_id:
                threading.Thread(target=route_action, args=(action_id,)).start()

# start the listener thread
listener_thread = threading.Thread(target=start_udp_server, daemon=True)
listener_thread.start()

# keyboard bindings
for i in range(1, 9):
    keyboard.add_hotkey(str(i), lambda idx=i: route_action(idx))

print("""
=========================================
Keyboard Control Menu - FNAF 2 
=========================================
[1] Toggle Camera Tablet (Right 'ok')
[2] Toggle Freddy Mask (Left 'palm')
[3] Check Left Vent / Nav Left
[4] Check Right Vent / Nav Right
[5] Flashlight (Right 'palm')
[6] Honk Nose / Nav Up
[7] Wind Music Box (Left 'ok')
[8] Nav Down ('two_down')
-----------------------------------------
Press keys 1-8 to perform actions
Press 'ESC' to exit
=========================================
""")

keyboard.wait('esc')