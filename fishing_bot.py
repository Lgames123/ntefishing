import cv2
import numpy as np
import mss
import win32gui
import win32process
import psutil
import ctypes
import ctypes.wintypes
import time
import keyboard
import sys
import win32con
import win32api

# ==============================================================================
# CONFIGURATION
# ==============================================================================
WINDOW_TITLE = "NTE  "
PROCESS_NAME = "HTGame.exe"
SHOW_DEBUG_WINDOW = True  # Set to True to show OpenCV visualization
SAFETY_MARGIN = 6          # Pixels from left/right bounds to start moving
LOOP_DELAY_DEFAULT = 0.05  # Seconds between frames when idling/waiting (saves CPU)
LOOP_DELAY_CATCHING = 0.001 # Seconds between frames during active catching (high refresh rate)

# Reference dimensions (DO NOT CHANGE)
REF_W = 3440
REF_H = 1440
REF_ROI_W = 1389
REF_ROI_H = 253
REF_ROI_X_START = 1025
REF_ROI_Y_START = 0

# HSV Thresholds
LOWER_YELLOW = np.array([15, 80, 80])
UPPER_YELLOW = np.array([35, 255, 255])
LOWER_GREEN = np.array([35, 50, 50])
UPPER_GREEN = np.array([90, 255, 255])

# ==============================================================================
# WIN32 KEYBOARD & MOUSE MESSAGE EMULATION
# ==============================================================================
# Virtual Keys
VK_A = 0x41
VK_D = 0x44
VK_F = 0x46
VK_SPACE = 0x20
VK_RETURN = 0x0D
VK_ESCAPE = 0x1B

# Scan Codes
SCAN_A = 0x1E
SCAN_D = 0x20
SCAN_F = 0x21
SCAN_SPACE = 0x39
SCAN_ENTER = 0x1C
SCAN_ESC = 0x01

# Win32 Message Constants
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP = 0x0202
MK_LBUTTON = 0x0001

# Track Key States
key_state = {"A": False, "D": False}
last_send_time = {"A": 0, "D": 0}

def update_keys(hwnd, a_down, d_down):
    """Sends key events directly to the window message queue using SendMessage."""
    if hwnd is None:
        return
        
    current_time = time.time()
    
    # Process 'A' key
    if a_down:
        if not key_state["A"] or (current_time - last_send_time["A"] > 0.01):
            lparam_down = 1 | (SCAN_A << 16)
            if key_state["A"]:
                lparam_down |= (1 << 30)
            win32gui.SendMessage(hwnd, WM_KEYDOWN, VK_A, lparam_down)
            key_state["A"] = True
            last_send_time["A"] = current_time
    else:
        if key_state["A"]:
            lparam_up = 1 | (SCAN_A << 16) | (1 << 30) | (1 << 31)
            win32gui.SendMessage(hwnd, WM_KEYUP, VK_A, lparam_up)
            key_state["A"] = False

    # Process 'D' key
    if d_down:
        if not key_state["D"] or (current_time - last_send_time["D"] > 0.01):
            lparam_down = 1 | (SCAN_D << 16)
            if key_state["D"]:
                lparam_down |= (1 << 30)
            win32gui.SendMessage(hwnd, WM_KEYDOWN, VK_D, lparam_down)
            key_state["D"] = True
            last_send_time["D"] = current_time
    else:
        if key_state["D"]:
            lparam_up = 1 | (SCAN_D << 16) | (1 << 30) | (1 << 31)
            win32gui.SendMessage(hwnd, WM_KEYUP, VK_D, lparam_up)
            key_state["D"] = False

def ensure_focus(hwnd):
    """Brings the window to the foreground if it is not already."""
    if hwnd is None:
        return
    try:
        foreground_hwnd = win32gui.GetForegroundWindow()
        if foreground_hwnd != hwnd:
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            win32gui.SetForegroundWindow(hwnd)
            time.sleep(0.15)  # Allow focus transition
            print("[INFO] Brought target window to foreground.")
    except Exception as e:
        print(f"[Warning] Failed to focus window: {e}")

def press_key_f(hwnd):
    """Sends a single keypress of F (down and up) to the window."""
    if hwnd is None:
        return
    ensure_focus(hwnd)
    lparam_down = 1 | (SCAN_F << 16)
    lparam_up = 1 | (SCAN_F << 16) | (1 << 30) | (1 << 31)
    win32gui.SendMessage(hwnd, WM_KEYDOWN, VK_F, lparam_down)
    time.sleep(0.08)  # brief hold delay
    win32gui.SendMessage(hwnd, WM_KEYUP, VK_F, lparam_up)
    print("[INFO] Hardware-emulated F keypress sent (Cast/Strike/Dismiss).")

def press_key_space(hwnd):
    """Sends a single keypress of Space (down and up) to the window."""
    if hwnd is None:
        return
    ensure_focus(hwnd)
    lparam_down = 1 | (SCAN_SPACE << 16)
    lparam_up = 1 | (SCAN_SPACE << 16) | (1 << 30) | (1 << 31)
    win32gui.SendMessage(hwnd, WM_KEYDOWN, VK_SPACE, lparam_down)
    time.sleep(0.08)  # brief hold delay
    win32gui.SendMessage(hwnd, WM_KEYUP, VK_SPACE, lparam_up)
    print("[INFO] Hardware-emulated SPACE keypress sent.")

def press_key_enter(hwnd):
    """Sends a single keypress of Enter (down and up) to the window."""
    if hwnd is None:
        return
    ensure_focus(hwnd)
    lparam_down = 1 | (SCAN_ENTER << 16)
    lparam_up = 1 | (SCAN_ENTER << 16) | (1 << 30) | (1 << 31)
    win32gui.SendMessage(hwnd, WM_KEYDOWN, VK_RETURN, lparam_down)
    time.sleep(0.08)  # brief hold delay
    win32gui.SendMessage(hwnd, WM_KEYUP, VK_RETURN, lparam_up)
    print("[INFO] Hardware-emulated ENTER keypress sent.")

def press_key_esc(hwnd):
    """Sends a single keypress of ESC (down and up) to the window."""
    if hwnd is None:
        return
    ensure_focus(hwnd)
    lparam_down = 1 | (SCAN_ESC << 16)
    lparam_up = 1 | (SCAN_ESC << 16) | (1 << 30) | (1 << 31)
    win32gui.SendMessage(hwnd, WM_KEYDOWN, VK_ESCAPE, lparam_down)
    time.sleep(0.08)  # brief hold delay
    win32gui.SendMessage(hwnd, WM_KEYUP, VK_ESCAPE, lparam_up)
    print("[INFO] Hardware-emulated ESC keypress sent (End Screen Dismiss).")

def click_window(hwnd, x, y):
    """Sends a mouse click using a hardware cursor teleport-click-restore sequence.
       Treats coordinates as client area relative; if x and y are None, clicks center."""
    if hwnd is None:
        return
    try:
        # Try to bring window to foreground and restore it
        foreground_hwnd = win32gui.GetForegroundWindow()
        if foreground_hwnd != hwnd:
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            win32gui.SetForegroundWindow(hwnd)
            time.sleep(0.2)  # Give Windows time to switch focus
            
        client_rect = win32gui.GetClientRect(hwnd)
        cl_w = client_rect[2]
        cl_h = client_rect[3]
        
        # Determine client x, y targets
        cx_val = x if x is not None else cl_w // 2
        cy_val = y if y is not None else cl_h // 2
        
        # Convert to screen coordinates
        cx, cy = win32gui.ClientToScreen(hwnd, (cx_val, cy_val))
        
        # Save, Click, and Restore
        orig_x, orig_y = win32gui.GetCursorPos()
        win32gui.SetCursorPos((cx, cy))
        time.sleep(0.05)
        
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        time.sleep(0.20)  # Robust 200ms hold delay for UE5
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
        time.sleep(0.05)
        
        win32gui.SetCursorPos((orig_x, orig_y))
        print(f"[INFO] Hardware client-click sent at screen ({cx}, {cy}) / client ({cx_val}, {cy_val}).")
    except Exception as e:
        print(f"[Warning] Click failed: {e}")

# ==============================================================================
# WINDOW AND SCANNING FUNCTIONS
# ==============================================================================
def find_nte_window():
    """Finds the HWND and screen Rect for the NTE / HTGame.exe window."""
    hwnd_list = []
    def winEnumHandler(hwnd, ctx):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title == WINDOW_TITLE:
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                try:
                    proc = psutil.Process(pid)
                    if proc.name().lower() == PROCESS_NAME.lower():
                        rect = win32gui.GetWindowRect(hwnd)
                        hwnd_list.append((hwnd, rect))
                except Exception:
                    pass
    win32gui.EnumWindows(winEnumHandler, None)
    return hwnd_list[0] if hwnd_list else None

def get_scaled_roi(window_rect):
    """Calculates the scaling factor and screen crop coordinates for any resolution."""
    x1, y1, x2, y2 = window_rect
    w = x2 - x1
    h = y2 - y1
    
    scale_x = w / float(REF_W)
    scale_y = h / float(REF_H)
    
    roi_w = int(REF_ROI_W * scale_x)
    roi_h = int(REF_ROI_H * scale_y)
    
    roi_x = x1 + (w - roi_w) // 2
    roi_y = y1
    
    return {
        "top": roi_y,
        "left": roi_x,
        "width": roi_w,
        "height": roi_h
    }

# Centered banner ROI at 3440x1440px reference
REF_BANNER_ROI_W = 1200
REF_BANNER_ROI_H = 600
REF_BANNER_ROI_X = 1120
REF_BANNER_ROI_Y = 420

def get_scaled_banner_roi(window_rect):
    """Calculates the screen crop coordinates for the central banner at any resolution."""
    x1, y1, x2, y2 = window_rect
    w = x2 - x1
    h = y2 - y1
    
    scale_x = w / float(REF_W)
    scale_y = h / float(REF_H)
    
    roi_w = int(REF_BANNER_ROI_W * scale_x)
    roi_h = int(REF_BANNER_ROI_H * scale_y)
    roi_x = x1 + int(REF_BANNER_ROI_X * scale_x)
    roi_y = y1 + int(REF_BANNER_ROI_Y * scale_y)
    
    return {
        "top": roi_y,
        "left": roi_x,
        "width": roi_w,
        "height": roi_h
    }

# ==============================================================================
# STATE, TOGGLE & INTERACTIVE GUI CALLBACKS
# ==============================================================================
bot_active = False
active_hwnd = None
should_exit = False  # Global flag set by the overlay EXIT button

def toggle_bot():
    global bot_active
    bot_active = not bot_active
    if bot_active:
        print("\n>>> [F9] BOT ACTIVATED (ON) <<<")
    else:
        print("\n>>> [F9] BOT DEACTIVATED (OFF) <<<")
        if active_hwnd:
            update_keys(active_hwnd, False, False)

def on_mouse_click(event, x, y, flags, param):
    """Callback for OpenCV window mouse events to detect Exit button click."""
    global should_exit
    if event == cv2.EVENT_LBUTTONDOWN:
        # Scale back to 1389x253 coords:
        # Close button is at x=[620, 684], y=[10, 40] on the scaled-down 694x126 debug overlay
        if 620 <= x <= 684 and 10 <= y <= 40:
            print("\n[INFO] Exit Button Clicked! Shutting down gracefully...")
            should_exit = True

# ==============================================================================
# ==============================================================================
# TEMPLATES & STATE MACHINE DEFINITIONS
# ==============================================================================
STATE_IDLE = "IDLE"                         # Hook icon is visible, ready to cast
STATE_CASTING = "CASTING"                   # Temporary state/cooldown after casting
STATE_WAITING_FOR_BITE = "WAITING_FOR_BITE" # Hook is cast, waiting for fish to bite
STATE_CATCHING = "CATCHING"                 # Keeping the yellow marker inside green bounds
STATE_END_SCREEN = "END_SCREEN"             # Fishing ended, waiting to click and close

try:
    template_idle = cv2.imread('resources/hook_idle.png')
    template_bite = cv2.imread('resources/hook_bite.png')
    template_bite_blue_ring = cv2.imread('resources/hook_bite_blue_ring.png')
    template_banner = cv2.imread('resources/fish_on_hook_banner.png')
    if template_idle is None or template_bite is None or template_bite_blue_ring is None or template_banner is None:
        print("[WARNING] Failed to load one or more resources/ templates!")
        print("Template matching may be incomplete or unavailable.")
except Exception as e:
    print(f"[WARNING] Error loading templates: {e}")

# ==============================================================================
# MAIN CONTROLLER LOOP
# ==============================================================================
def main():
    global bot_active, active_hwnd, should_exit
    print("=========================================================")
    print("      FISHING BOT (ALWAYS-ON-TOP & STATE MACHINE) - NTE  ")
    print("=========================================================")
    print("Instructions:")
    print("  1. Press [F9] to Toggle the Bot ON or OFF.")
    print("  2. Click the red [EXIT] button on the overlay or press [Esc] to Quit.")
    print("=========================================================")

    # Check if running as Admin
    is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
    print(f"Running as Administrator: {'YES (Good)' if is_admin else 'NO (Warning!)'}")
    if not is_admin:
        print("\n[WARNING] This script is NOT running as Administrator!")
        print("Please restart your terminal/IDE as Administrator to avoid UAC privilege blocks.")
        print("=========================================================\n")

    # Register hotkey toggle
    keyboard.add_hotkey('F9', toggle_bot)
    
    window_found_last = True
    window_created = False
    
    # State Machine state variables
    current_state = STATE_IDLE
    state_cooldown_until = 0.0
    catching_started_time = 0.0
    catching_lost_detection_start = 0.0
    catching_ended_time = 0.0
    
    max_val_idle = 0.0
    max_val_bite = 0.0
    max_val_blue_ring = 0.0
    max_val_banner = 0.0
    
    try:
        with mss.mss() as sct:
            while not should_exit:
                # 1. Find window
                win_info = find_nte_window()
                if not win_info:
                    if window_found_last:
                        print(f"[Warning] Window '{WINDOW_TITLE}' not found. Waiting for game...")
                        window_found_last = False
                        if active_hwnd:
                            update_keys(active_hwnd, False, False)
                    time.sleep(1.0)
                    continue
                
                if not window_found_last:
                    print(f"[Success] Found window '{WINDOW_TITLE}'. Capturing...")
                    window_found_last = True
                
                hwnd, rect = win_info
                active_hwnd = hwnd
                
                x1, y1, x2, y2 = rect
                win_w = x2 - x1
                win_h = y2 - y1
                
                current_time = time.time()
                
                # Check if bot is deactivated
                if not bot_active:
                    update_keys(hwnd, False, False)
                    current_state = STATE_IDLE
                    state_cooldown_until = 0.0
                    catching_lost_detection_start = 0.0
                
                # Initialize detection variables
                yellow_marker = None
                green_rect = None
                img = None
                max_val_idle = 0.0
                max_val_bite = 0.0
                max_val_blue_ring = 0.0
                max_val_banner = 0.0
                
                # 2. Dynamic State-Driven Captures
                if current_state == STATE_CATCHING:
                    # Capture dynamic ROI (fishing bar) ONLY during catching
                    monitor = get_scaled_roi(rect)
                    try:
                        screenshot = np.array(sct.grab(monitor))
                    except Exception:
                        update_keys(hwnd, False, False)
                        time.sleep(0.5)
                        continue
                        
                    roi_bgr = cv2.cvtColor(screenshot, cv2.COLOR_BGRA2BGR)
                    img = cv2.resize(roi_bgr, (REF_ROI_W, REF_ROI_H), interpolation=cv2.INTER_LINEAR)
                    
                    # HSV masking for fishing bar
                    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
                    yellow_mask = cv2.inRange(hsv, LOWER_YELLOW, UPPER_YELLOW)
                    green_mask = cv2.inRange(hsv, LOWER_GREEN, UPPER_GREEN)
                    
                    # Contour detection for fishing bar
                    yellow_contours, _ = cv2.findContours(yellow_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                    green_contours, _ = cv2.findContours(green_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                    
                    # Filter Yellow Marker
                    for cnt in yellow_contours:
                        x, y, w, h = cv2.boundingRect(cnt)
                        aspect_ratio = h / float(w) if w > 0 else 0
                        area = cv2.contourArea(cnt)
                        if aspect_ratio > 1.5 and w < 20 and 50 < area < 500:
                            yellow_marker = (x, y, w, h)
                            break
                            
                    # Filter Green Rectangle
                    max_green_area = -1
                    for cnt in green_contours:
                        x, y, w, h = cv2.boundingRect(cnt)
                        aspect_ratio = w / float(h) if h > 0 else 0
                        area = cv2.contourArea(cnt)
                        if aspect_ratio > 2.0 and w > 50 and area > 500:
                            if area > max_green_area:
                                max_green_area = area
                                green_rect = (x, y, w, h)
                                
                elif current_state == STATE_IDLE:
                    # Capture HUD region ONLY when idle to detect cast readiness
                    scale_x = win_w / float(REF_W)
                    scale_y = win_h / float(REF_H)
                    
                    hud_w = int(1032 * scale_x)
                    hud_h = int(576 * scale_y)
                    hud_x = int(2408 * scale_x)
                    hud_y = int(864 * scale_y)
                    
                    hud_monitor = {
                        "top": y1 + hud_y,
                        "left": x1 + hud_x,
                        "width": hud_w,
                        "height": hud_h
                    }
                    
                    if template_idle is not None:
                        try:
                            hud_grab = np.array(sct.grab(hud_monitor))
                            hud_bgr = cv2.cvtColor(hud_grab, cv2.COLOR_BGRA2BGR)
                            hud_resized = cv2.resize(hud_bgr, (1032, 576), interpolation=cv2.INTER_LINEAR)
                            
                            # Match Idle
                            res_idle = cv2.matchTemplate(hud_resized, template_idle, cv2.TM_CCOEFF_NORMED)
                            _, max_val_idle, _, _ = cv2.minMaxLoc(res_idle)
                        except Exception:
                            pass
                            
                elif current_state == STATE_WAITING_FOR_BITE:
                    # Capture HUD and Banner regions ONLY when waiting for a bite
                    scale_x = win_w / float(REF_W)
                    scale_y = win_h / float(REF_H)
                    
                    # Bounding box for HUD
                    hud_w = int(1032 * scale_x)
                    hud_h = int(576 * scale_y)
                    hud_x = int(2408 * scale_x)
                    hud_y = int(864 * scale_y)
                    
                    hud_monitor = {
                        "top": y1 + hud_y,
                        "left": x1 + hud_x,
                        "width": hud_w,
                        "height": hud_h
                    }
                    
                    # Bounding box for Central Banner
                    banner_monitor = get_scaled_banner_roi(rect)
                    
                    # Match Hook templates in HUD
                    if template_bite is not None or template_bite_blue_ring is not None:
                        try:
                            hud_grab = np.array(sct.grab(hud_monitor))
                            hud_bgr = cv2.cvtColor(hud_grab, cv2.COLOR_BGRA2BGR)
                            hud_resized = cv2.resize(hud_bgr, (1032, 576), interpolation=cv2.INTER_LINEAR)
                            
                            # Match standard flashing bite
                            if template_bite is not None:
                                res_bite = cv2.matchTemplate(hud_resized, template_bite, cv2.TM_CCOEFF_NORMED)
                                _, score_bite, _, _ = cv2.minMaxLoc(res_bite)
                                max_val_bite = score_bite
                                
                            # Match blue-ringed bite
                            if template_bite_blue_ring is not None:
                                res_blue_ring = cv2.matchTemplate(hud_resized, template_bite_blue_ring, cv2.TM_CCOEFF_NORMED)
                                _, score_blue_ring, _, _ = cv2.minMaxLoc(res_blue_ring)
                                max_val_blue_ring = score_blue_ring
                        except Exception:
                            pass
                            
                    # Match Central Banner template
                    if template_banner is not None:
                        try:
                            banner_grab = np.array(sct.grab(banner_monitor))
                            banner_bgr = cv2.cvtColor(banner_grab, cv2.COLOR_BGRA2BGR)
                            banner_resized = cv2.resize(banner_bgr, (1200, 600), interpolation=cv2.INTER_LINEAR)
                            
                            res_banner = cv2.matchTemplate(banner_resized, template_banner, cv2.TM_CCOEFF_NORMED)
                            _, max_val_banner, _, _ = cv2.minMaxLoc(res_banner)
                        except Exception:
                            pass
                
                # 3. State Machine Processing (when active)
                action = "WAITING"
                if bot_active:
                    in_cooldown = current_time < state_cooldown_until
                    
                    if not in_cooldown:
                        if current_state == STATE_IDLE:
                            if max_val_idle > 0.78:
                                print(f"[STATE] Idle Hook detected ({max_val_idle:.2f}). Casting hook (Press F)...")
                                press_key_f(hwnd)
                                current_state = STATE_CASTING
                                state_cooldown_until = current_time + 2.0  # 2s cooldown for cast
                                
                        elif current_state == STATE_CASTING:
                            # Cooldown has finished, move to waiting
                            current_state = STATE_WAITING_FOR_BITE
                            print("[STATE] Transitioning to WAITING FOR BITE...")
                            
                        elif current_state == STATE_WAITING_FOR_BITE:
                            is_bite = (max_val_blue_ring > 0.95) or (max_val_banner > 0.78)
                            if is_bite:
                                if max_val_blue_ring > 0.95:
                                    print(f"[STATE] Bite Hook (Blue Ring) detected ({max_val_blue_ring:.2f})! Striking (Press F)...")
                                else:
                                    print(f"[STATE] Central Banner detected ({max_val_banner:.2f})! Striking (Press F)...")
                                    
                                press_key_f(hwnd)
                                current_state = STATE_CATCHING
                                catching_started_time = current_time
                                catching_lost_detection_start = 0.0
                                print("[STATE] Transitioned DIRECTLY to CATCHING state.")
                                
                        elif current_state == STATE_CATCHING:
                            in_grace_period = (current_time - catching_started_time < 3.0)
                            
                            if yellow_marker and green_rect:
                                catching_lost_detection_start = 0.0  # Reset lost detection
                                yx = yellow_marker[0] + yellow_marker[2] / 2.0
                                gx_left = green_rect[0]
                                gx_right = green_rect[0] + green_rect[2]
                                
                                if yx < gx_left + SAFETY_MARGIN:
                                    action = "PULL RIGHT"
                                elif yx > gx_right - SAFETY_MARGIN:
                                    action = "PULL LEFT"
                                else:
                                    action = "STAY"
                            else:
                                if in_grace_period:
                                    # Grace period: let UI load, maintain status quo
                                    action = "STAY"
                                else:
                                    # Lost detection temporarily, check if sustained
                                    if catching_lost_detection_start == 0.0:
                                        catching_lost_detection_start = current_time
                                    elif current_time - catching_lost_detection_start >= 1.5:
                                        print("[STATE] Fishing minigame ended (detection lost). Transitioning to END_SCREEN...")
                                        update_keys(hwnd, False, False)
                                        current_state = STATE_END_SCREEN
                                        catching_ended_time = current_time
                                        
                        elif current_state == STATE_END_SCREEN:
                            if current_time - catching_ended_time >= 5.0:
                                print("[STATE] End-screen wait completed. Sending ESC keypress to dismiss screen...")
                                press_key_esc(hwnd)
                                current_state = STATE_IDLE
                                state_cooldown_until = current_time + 2.5  # 2.5s cooldown to let HUD load
                
                # 4. Apply Key Inputs (if in Catching phase and active)
                if bot_active and current_state == STATE_CATCHING:
                    if action == "PULL LEFT":
                        update_keys(hwnd, True, False)
                    elif action == "PULL RIGHT":
                        update_keys(hwnd, False, True)
                    else:
                        update_keys(hwnd, False, False)
                else:
                    update_keys(hwnd, False, False)
                
                # 5. Visualization Overlay
                if SHOW_DEBUG_WINDOW:
                    if current_state == STATE_CATCHING and img is not None:
                        vis = img.copy()
                        # Draw Green Bounds
                        if green_rect:
                            x, y, w, h = green_rect
                            cv2.rectangle(vis, (x, y), (x+w, y+h), (0, 255, 0), 2)
                            cv2.putText(vis, "Green Bounds", (x, y-7), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                            # Draw safety margins
                            cv2.line(vis, (x + SAFETY_MARGIN, y), (x + SAFETY_MARGIN, y+h), (0, 200, 200), 1, cv2.LINE_AA)
                            cv2.line(vis, (x + w - SAFETY_MARGIN, y), (x + w - SAFETY_MARGIN, y+h), (0, 200, 200), 1, cv2.LINE_AA)
                        
                        # Draw Yellow Marker
                        if yellow_marker:
                            x, y, w, h = yellow_marker
                            cv2.rectangle(vis, (x, y), (x+w, y+h), (0, 0, 255), 2)
                            cv2.putText(vis, "Marker", (x, y-7), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
                    else:
                        # Non-catching states get a black dashboard background
                        vis = np.zeros((REF_ROI_H, REF_ROI_W, 3), dtype=np.uint8)
                        
                    # Draw Interactive Close Button [EXIT] at top right
                    cv2.rectangle(vis, (1240, 20), (1368, 80), (50, 50, 220), -1, cv2.LINE_AA)  # Red background
                    cv2.rectangle(vis, (1240, 20), (1368, 80), (255, 255, 255), 2, cv2.LINE_AA)  # White border
                    cv2.putText(vis, "EXIT", (1270, 58), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)
                    
                    # Status text
                    status_color = (0, 255, 0) if bot_active else (0, 165, 255)
                    status_text = "BOT ACTIVE (ON)" if bot_active else "BOT STANDBY (OFF)"
                    
                    cv2.putText(vis, f"Status: {status_text} (Press F9)", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, status_color, 2)
                    cv2.putText(vis, f"State: {current_state}", (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                    cv2.putText(vis, f"Action: {action}", (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                    
                    # Match correlation diagnostics
                    cv2.putText(vis, f"Idle: {max_val_idle:.2f}  Bite: {max_val_bite:.2f}  Ring: {max_val_blue_ring:.2f}  Banner: {max_val_banner:.2f}", 
                                (20, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
                    
                    # Draw countdown timer info if in cooldown or waiting
                    if bot_active:
                        if current_time < state_cooldown_until:
                            rem = max(0.0, state_cooldown_until - current_time)
                            cv2.putText(vis, f"Cooldown: {rem:.1f}s", (20, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 165, 255), 1)
                        elif current_state == STATE_END_SCREEN:
                            rem = max(0.0, 5.0 - (current_time - catching_ended_time))
                            cv2.putText(vis, f"Auto-Click in: {rem:.1f}s", (20, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
                        elif current_state == STATE_CATCHING and (current_time - catching_started_time < 3.0):
                            rem = max(0.0, 3.0 - (current_time - catching_started_time))
                            cv2.putText(vis, f"Grace Period: {rem:.1f}s", (20, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                    
                    # Resize to half footprint
                    debug_show = cv2.resize(vis, (REF_ROI_W // 2, REF_ROI_H // 2))
                    cv2.imshow("NTE Fishing Bot - Debug Overlay", debug_show)
                    
                    # Force window to be ALWAYS ON TOP (Topmost)
                    if not window_created:
                        cv2.setMouseCallback("NTE Fishing Bot - Debug Overlay", on_mouse_click)
                        hwnd_vis = win32gui.FindWindow(None, "NTE Fishing Bot - Debug Overlay")
                        if hwnd_vis:
                            win32gui.SetWindowPos(hwnd_vis, win32con.HWND_TOPMOST, 0, 0, 0, 0,
                                                  win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE)
                            window_created = True
                    
                    # Handle Esc key to close debug window
                    if cv2.waitKey(1) & 0xFF == 27:
                        print("\nExiting bot loop...")
                        break
                
                # 6. Dynamic Polling Rate: sleep based on active catching state
                active_delay = LOOP_DELAY_CATCHING if current_state == STATE_CATCHING else LOOP_DELAY_DEFAULT
                time.sleep(active_delay)
                
    except KeyboardInterrupt:
        print("\nStopping bot...")
    finally:
        # Clean up
        if active_hwnd:
            update_keys(active_hwnd, False, False)
        cv2.destroyAllWindows()
        print("Bot stopped successfully. All inputs released.")

if __name__ == '__main__':
    main()
