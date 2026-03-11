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
    7: 0, #up
    8: 1, #down
    5: 2, #right
    2: 3, #left
}

# maps cameras to their directional neighbors (up, down, right, left)
cam_direction_map = {
    "1A": ["0", "1B", "0", "0"],
    "1B": ["1A", "1C", "7", "5"],
    "1C": ["1B", "3", "7", "5"],
    "2A": ["1C", "2B", "4A", "3"],
    "2B": ["2A", "0", "4N", "0"],
    "3":  ["1C", "0", "2A", "0"],
    "4A": ["6", "4B", "6", "2A"],
    "4B": ["4A", "0", "0", "2B"],
    "5":  ["1B", "1C", "1B", "0"],
    "6":  ["7", "4A", "0", "4A"],
    "7":  ["1A", "6", "0", "1B"],
}

#TODO: finish the formatting
cam_pixel_map = {
    "1A": (1224, 435),
    "1B": (1200, 505),
    # Cam 1C: (1159, 604)
    # Cam 2A: (1223, 746)
    # Cam 2B: (1228, 799)
    # Cam 3: (1119, 724)
    # Cam 4A: (1354, 748)
    # Cam 4B: (1359, 800)
    # Cam 5: (1068, 544)
    # Cam 6: (1483, 705)
    # Cam 7: (1488, 536)
}

in_camera = False
curr_cam = "1A"

def get_action_id(hand, gesture):
    """
    Evaluates the hand and gesture to determine the correct action ID.
    If no hand is specified in the rule, it works for 'Left' or 'Right'.
    """
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
    return None # Returns None if the combination doesn't match any rules

def camera_action(action_id):
    if action_id == 1:
        #TODO: toggle camera tablet off, then set in_camera to false
    
    else:
        if action_id not in direction_index:
            print(f"Invalid camera action ID: {action_id}")
            return #TODO: do we want to handle this action on the main screen by closing the tablet then attempting the action?
        else:
            direction = direction_index[action_id]
            camera = #TODO: set camera using cam_map
            curr_cam = camera # set new curr camera 
            #TODO call py autogui to click the correct camera pixel


def fnaf_action(action_id):
    """Executes mouse movements for a given action in FNAF, based on input ID (key pressed)."""
    if action_id == 1:
        print("Action 1: Toggling Camera Tablet")
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
        
        # Split the string "Hand:Gesture" into two variables
        if ":" in payload:
            hand, gesture = payload.split(":", 1)
            
            # Run it through the logic check
            action_id = get_action_id(hand, gesture)
            
            if action_id:
                if in_camera:
                    #TODO: handle camera actions in the camera action function
                else:
                    threading.Thread(target=fnaf_action, args=(action_id,)).start()

# Start the listener thread in the background
listener_thread = threading.Thread(target=start_udp_server, daemon=True)
listener_thread.start()

# keyboard bindings for FNAF actions 1-7
keyboard.add_hotkey('1', lambda: fnaf_action(1))
keyboard.add_hotkey('2', lambda: fnaf_action(2))
keyboard.add_hotkey('3', lambda: fnaf_action(3))
keyboard.add_hotkey('4', lambda: fnaf_action(4))
keyboard.add_hotkey('5', lambda: fnaf_action(5))
keyboard.add_hotkey('6', lambda: fnaf_action(6))
keyboard.add_hotkey('7', lambda: fnaf_action(7))

print("""
=========================================
Keyboard Control Menu - Five Nights at Freddy's  
=========================================
[1] Toggle Camera Tablet
[2] Toggle Left Door
[3] Flash Left Light (0.5s)
[4] Toggle Right Door
[5] Flash Right Light (0.5s)
[6] Mute Phone Guy
[7] Honk Freddy's Nose 
-----------------------------------------
Press keys 1-7 to perform actions
Press 'ESC' to exit
=========================================
""")

keyboard.wait('esc')