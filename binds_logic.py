"""
binds_logic.py - Contains the logic for handling keyboard bindings and mapping them to FNAF actions based
on inference results from the computer vision gesture model.

Usage:
    python binds_logic.py
"""
import pyautogui
import time
import keyboard
import socket
import threading

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

# maps actions to camera directions for cam_direction_map (up, down, right, left)
direction_index = {
    7: 0, # up
    8: 1, # down
    5: 2, # right
    3: 3, # left 
}

# maps cameras to their directional neighbors (up, down, right, left)
cam_direction_map = {
    "1A": ["0", "1B", "0", "0"],
    "1B": ["1A", "1C", "7", "5"],
    "1C": ["1B", "3", "7", "5"],
    "2A": ["1C", "2B", "4A", "3"],
    "2B": ["2A", "0", "4B", "0"], # changed 4N to 4B assuming typo
    "3":  ["1C", "0", "2A", "0"],
    "4A": ["6", "4B", "6", "2A"],
    "4B": ["4A", "0", "0", "2B"],
    "5":  ["1B", "1C", "1B", "0"],
    "6":  ["7", "4A", "0", "4A"],
    "7":  ["1A", "6", "0", "1B"],
}

# camera pixel coordinates
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

in_camera = False
curr_cam = "1A"

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
            print(f"Invalid camera action ID: {action_id}")
            return 
        
        dir_idx = direction_index[action_id]
        new_cam = cam_direction_map[curr_cam][dir_idx]
        
        if new_cam != "0":
            print(f"Camera Nav: {curr_cam} -> {new_cam}")
            curr_cam = new_cam
            target_x, target_y = cam_pixel_map[curr_cam]
            pyautogui.click(target_x, target_y)
        else:
            print(f"Cannot move in that direction from {curr_cam}.")

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
        print("Action 3: Flashing Left Light (0.5s)")
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
        print("Action 5: Flashing Right Light (0.5s)")
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

def start_udp_server():
    """Listens for incoming network gestures and parses handedness."""
    UDP_IP = "0.0.0.0" 
    UDP_PORT = 5005
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))
    
    print(f"\n[NETWORK] UDP Server actively listening on port {UDP_PORT}...")
    
    while True:
        data, addr = sock.recvfrom(1024) 
        payload = data.decode('utf-8')
        print(f"[NETWORK] Received payload: '{payload}' from {addr[0]}")
        
        if ":" in payload:
            hand, gesture = payload.split(":", 1)
            action_id = get_action_id(hand, gesture)
            
            if action_id:
                threading.Thread(target=route_action, args=(action_id,)).start()

listener_thread = threading.Thread(target=start_udp_server, daemon=True)
listener_thread.start()

# action keyboard binds
keyboard.add_hotkey('1', lambda: route_action(1))
keyboard.add_hotkey('2', lambda: route_action(2))
keyboard.add_hotkey('3', lambda: route_action(3))
keyboard.add_hotkey('4', lambda: route_action(4))
keyboard.add_hotkey('5', lambda: route_action(5))
keyboard.add_hotkey('6', lambda: route_action(6))
keyboard.add_hotkey('7', lambda: route_action(7))
keyboard.add_hotkey('8', lambda: route_action(8)) # added bind for navigating down in camera view

print("""
=========================================
Keyboard Control Menu - Five Nights at Freddy's  
=========================================
[1] Toggle Camera Tablet
[2] Toggle Left Door / Navigate Left
[3] Flash Left Light / Navigate Left
[4] Toggle Right Door / Navigate Right
[5] Flash Right Light / Navigate Right
[6] Mute Phone Guy
[7] Honk Freddy's Nose / Navigate Up
[8] Navigate Down
-----------------------------------------
Press keys 1-8 to perform actions
Press 'ESC' to exit
=========================================
""")

keyboard.wait('esc')