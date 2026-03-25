# Real-Time Computer Vision Game Controller for Five Nights at Freddy's

A real-time, gesture-based controller for *Five Nights at Freddy's*, powered by a custom-trained AI model and a low-latency network architecture. 

A dedicated machine runs a computer vision pipeline to classify hand gestures via webcam, and sends the recognized actions over a local network via UDP sockets to a second machine running the game, which executes the actions using PyAutoGUI.

## Model Architecture & Vision Pipeline
* **Classification:** Uses ResNet18 fine-tuned for hand gesture classification.
* **Localization:** Hand detection and bounding box cropping are handled by MediaPipe. The ResNet18 model only classifies the isolated, cropped hand region.
* **Classes:** `palm`, `mute`, `ok`, and `two_up`. 
* **Augmentation:** The last few classes were augmented by rotating the `two_up` class by 90, 180, and 270 degrees. These classes were relabeled as `two_sideways_right`, `two_sideways_left`, and `two_down`. 
* **Confidence Threshold:** Displays as "Unknown" if the model's confidence prediction falls below 55%.

## Gesture Control Mapping
The logic dynamically changes depending on whether the in-game Camera Tablet is currently open or closed. Handedness (Left/Right) is strictly enforced for door controls to create an intuitive physical experience.

| Action | Required Gesture | Allowed Hand |
| :--- | :--- | :--- |
| **Toggle Camera Tablet** | `ok` | Left or Right |
| **Toggle Left Door** | `palm` | **Left Only** |
| **Toggle Right Door** | `palm` | **Right Only** |
| **Flash Left Light** | `two_sideways_left` | Left or Right |
| **Flash Right Light** | `two_sideways_right` | Left or Right |
| **Mute Phone Guy** | `mute` | Left or Right |
| **Honk Freddy's Nose** | `two_up` | Left or Right |

**Camera Navigation Mode:**
When the Camera Tablet is active, directional gestures (`two_up`, `two_down`, `two_sideways_left`, `two_sideways_right`) are repurposed to navigate between adjacent camera feeds using a custom directional hashmap, allowing us to navigate to each camera's directional neighbors (which camera is closest on the left, right, up, and down).

## Setup Instructions

**Prerequisites:** 
* Python 3.12 is required (PyTorch currently does not support Python 3.13+).
* Two computers connected to the same local Wi-Fi network

**Environment Setup (Run on both machines):**
```bash
python3.12 -m venv venv
source venv/bin/activate  
pip install --upgrade pip
pip install -r requirements.txt
```

**Network Configuration:**
Before running, you must point the AI client to the game server.
1. Find the local IPv4 address of the computer running the game.
2. Open `webcam_gesture_demo.py` on a seperate machine.
3. Update the `UDP_IP` variable to match Computer 2's IP address.

## Running the Project

Because this uses a client-server architecture, the game server must be listening *before* the AI client starts sending data.

**Step 1: Start the Game Server (Computer 2)**

Open the game in fullscreen, and in your activated environment, run:
```bash
python binds_logic.py
```
*(Note: You may need to grant Python permission through Windows Defender/Firewall to receive UDP packets).*

**Step 2: Start the CV Client (Computer 1)**

In your activated environment, run:
```bash
python webcam_gesture_demo.py
```
Press `q` to quit the webcam feed. Press `esc` to terminate the game server.

## Limitations 
* **Resolution Dependency:** `pyautogui` relies on absolute, hardcoded pixel coordinates. The current `binds_logic.py` script is calibrated strictly for a `1920x1200` fullscreen window. Running the game at different resolutions will result in missed clicks, and appropriate configuration for each different resolution is required.
* **Lighting Sensitivity:** As with most standard RGB computer vision models, extreme low-light environments or heavy backlighting can reduce the accuracy of MediaPipe's hand tracking.
