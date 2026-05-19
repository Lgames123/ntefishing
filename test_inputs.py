import ctypes
import ctypes.wintypes
import time
import win32gui
import win32process
import psutil
import win32api
import win32con
import sys

# ==============================================================================
# CONFIGURATION
# ==============================================================================
WINDOW_TITLE = "NTE  "
PROCESS_NAME = "HTGame.exe"

# Virtual Keys
VK_A = 0x41
VK_D = 0x44

# Scan Codes
SCAN_A = 0x1E
SCAN_D = 0x20

# DirectInput Structure Definitions
wintypes = ctypes.wintypes

class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(wintypes.ULONG))
    ]

class INPUT_I(ctypes.Union):
    _fields_ = [
        ("ki", KEYBDINPUT),
        ("mi", ctypes.c_byte * 32), # Padding
        ("hi", ctypes.c_byte * 32)
    ]

class INPUT(ctypes.Structure):
    _fields_ = [
        ("type", wintypes.DWORD),
        ("ii", INPUT_I)
    ]

SendInput = ctypes.windll.user32.SendInput
INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_SCANCODE = 0x0008

def send_input_press(scan_code):
    extra = ctypes.c_ulong(0)
    ii_ = INPUT_I()
    ii_.ki = KEYBDINPUT(0, scan_code, KEYEVENTF_SCANCODE, 0, ctypes.pointer(extra))
    x = INPUT(INPUT_KEYBOARD, ii_)
    SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))

def send_input_release(scan_code):
    extra = ctypes.c_ulong(0)
    ii_ = INPUT_I()
    ii_.ki = KEYBDINPUT(0, scan_code, KEYEVENTF_SCANCODE | KEYEVENTF_KEYUP, 0, ctypes.pointer(extra))
    x = INPUT(INPUT_KEYBOARD, ii_)
    SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))

# ==============================================================================
# DIAGNOSTIC METHODS
# ==============================================================================

def test_direct_input_with_hold(hwnd, duration=1.0):
    """Method 1: DirectInput SendInput with a sustained hold duration."""
    print(f"--> Testing Method 1: DirectInput SendInput (Holding 'A' for {duration}s)...")
    # Bring window to foreground to ensure focus
    win32gui.SetForegroundWindow(hwnd)
    time.sleep(0.5)
    
    send_input_press(SCAN_A)
    time.sleep(duration)
    send_input_release(SCAN_A)
    print("Done Method 1.")

def test_keybd_event(hwnd, duration=1.0):
    """Method 2: Standard win32 keybd_event API (older but sometimes less hooked)."""
    print(f"--> Testing Method 2: win32 keybd_event (Holding 'A' for {duration}s)...")
    win32gui.SetForegroundWindow(hwnd)
    time.sleep(0.5)
    
    # 0 = KeyDown
    win32api.keybd_event(VK_A, SCAN_A, 0, 0)
    time.sleep(duration)
    # KEYEVENTF_KEYUP = 2
    win32api.keybd_event(VK_A, SCAN_A, win32con.KEYEVENTF_KEYUP, 0)
    print("Done Method 2.")

def test_post_message(hwnd, duration=1.0):
    """Method 3: PostMessage directly to the window message queue (does not require focus!)."""
    print(f"--> Testing Method 3: win32 PostMessage (Sending keydown 'A' for {duration}s)...")
    
    lparam_down = 1 | (SCAN_A << 16)
    lparam_up = 1 | (SCAN_A << 16) | (1 << 30) | (1 << 31)
    
    # We can post keydown messages repeatedly to simulate holding
    start_time = time.time()
    while time.time() - start_time < duration:
        win32gui.PostMessage(hwnd, win32con.WM_KEYDOWN, VK_A, lparam_down)
        time.sleep(0.05) # repeat every 50ms
        
    win32gui.PostMessage(hwnd, win32con.WM_KEYUP, VK_A, lparam_up)
    print("Done Method 3.")

def test_send_message(hwnd, duration=1.0):
    """Method 4: SendMessage directly to the window (synchronous window message)."""
    print(f"--> Testing Method 4: win32 SendMessage (Sending keydown 'A' for {duration}s)...")
    
    lparam_down = 1 | (SCAN_A << 16)
    lparam_up = 1 | (SCAN_A << 16) | (1 << 30) | (1 << 31)
    
    start_time = time.time()
    while time.time() - start_time < duration:
        win32gui.SendMessage(hwnd, win32con.WM_KEYDOWN, VK_A, lparam_down)
        time.sleep(0.05)
        
    win32gui.SendMessage(hwnd, win32con.WM_KEYUP, VK_A, lparam_up)
    print("Done Method 4.")

def test_pyautogui(hwnd, duration=1.0):
    """Method 5: PyAutoGUI (Virtual key simulation)."""
    print(f"--> Testing Method 5: pyautogui (Holding 'a' for {duration}s)...")
    try:
        import pyautogui
        win32gui.SetForegroundWindow(hwnd)
        time.sleep(0.5)
        pyautogui.keyDown('a')
        time.sleep(duration)
        pyautogui.keyUp('a')
        print("Done Method 5.")
    except Exception as e:
        print(f"Failed to run Method 5: {e}")

# ==============================================================================
# WINDOW SEARCH
# ==============================================================================
def find_nte_window():
    hwnd_list = []
    def winEnumHandler(hwnd, ctx):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title == WINDOW_TITLE:
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                try:
                    proc = psutil.Process(pid)
                    if proc.name().lower() == PROCESS_NAME.lower():
                        hwnd_list.append((hwnd, title))
                except Exception:
                    pass
    win32gui.EnumWindows(winEnumHandler, None)
    return hwnd_list[0] if hwnd_list else None

# ==============================================================================
# RUN DIAGNOSTICS
# ==============================================================================
def main():
    print("=========================================================")
    print("        INPUT DIAGNOSTICS FOR HTGAME.EXE ('NTE  ')       ")
    print("=========================================================")
    
    # Check if running as Admin
    is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
    print(f"Running as Administrator: {'YES (Good)' if is_admin else 'NO (Warning!)'}")
    if not is_admin:
        print("\n[WARNING] This script is NOT running as Administrator!")
        print("HTGame.exe runs with high privileges, and Windows will block")
        print("all keystrokes from a normal-privilege python script.")
        print("Please restart your terminal/IDE as Administrator and run again.")
        print("=========================================================\n")
    
    win_info = find_nte_window()
    if not win_info:
        print(f"Error: Window '{WINDOW_TITLE}' (HTGame.exe) not found!")
        print("Please start the game, make sure it is not minimized, and run this script again.")
        sys.exit(1)
        
    hwnd, title = win_info
    print(f"Found Window: HWND={hwnd}, Title='{title}'\n")
    
    print("We will now test 5 different input methods to see which one works.")
    print("Make sure you are in a text chat or in the fishing minigame")
    print("where holding 'A' would move the bar, character, or type 'a's.")
    print("There will be a 3-second countdown before each method...")
    
    methods = [
        ("Method 1: DirectInput SendInput (Scan Codes)", test_direct_input_with_hold),
        ("Method 2: win32 keybd_event API", test_keybd_event),
        ("Method 3: win32 PostMessage (Background)", test_post_message),
        ("Method 4: win32 SendMessage (Background)", test_send_message),
        ("Method 5: PyAutoGUI", test_pyautogui)
    ]
    
    for i, (name, func) in enumerate(methods, 1):
        print(f"\n--- Ready to test {name} ---")
        print("Starting in 3...")
        time.sleep(1.0)
        print("Starting in 2...")
        time.sleep(1.0)
        print("Starting in 1...")
        time.sleep(1.0)
        
        try:
            func(hwnd, duration=1.5)
        except Exception as e:
            print(f"Error during {name}: {e}")
            
    print("\n=========================================================")
    print("Diagnostics complete! Which method actually moved your character")
    print("or typed 'a' in the chat? Let me know so we can update the bot!")
    print("=========================================================")

if __name__ == '__main__':
    main()
