import cv2
import numpy as np
import mss
import win32gui
import win32process
import psutil

def find_nte_window():
    hwnd_list = []
    def winEnumHandler(hwnd, ctx):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title == "NTE  ":
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                try:
                    proc = psutil.Process(pid)
                    if proc.name() == "HTGame.exe":
                        hwnd_list.append((hwnd, rect_to_dict(win32gui.GetWindowRect(hwnd))))
                except Exception:
                    pass
    win32gui.EnumWindows(winEnumHandler, None)
    return hwnd_list[0] if hwnd_list else None

def rect_to_dict(rect):
    return {"left": rect[0], "top": rect[1], "right": rect[2], "bottom": rect[3], "width": rect[2]-rect[0], "height": rect[3]-rect[1]}

def test_capture_and_match():
    win_info = find_nte_window()
    if not win_info:
        print("HTGame.exe window 'NTE  ' not found.")
        return
        
    hwnd, rect = win_info
    print(f"Found window: HWND {hwnd}, Rect: {rect}")
    
    # Load template
    template = cv2.imread('resources/fishing.png')
    if template is None:
        print("Template resources/fishing.png not found!")
        return
    th, tw, tc = template.shape
    print(f"Template shape: {tw}x{th}")
    
    # Capture the entire screen or window region using mss
    with mss.mss() as sct:
        # We can capture the monitor containing the window or just the window rect
        # Since it is fullscreen/borderless at (0, 0, 3440, 1440), let's capture that region
        monitor = {
            "top": rect["top"],
            "left": rect["left"],
            "width": rect["width"],
            "height": rect["height"]
        }
        
        print(f"Capturing region: {monitor}")
        screenshot = np.array(sct.grab(monitor))
        # mss returns BGRA, convert to BGR for OpenCV
        screenshot = cv2.cvtColor(screenshot, cv2.COLOR_BGRA2BGR)
        
        # Match template
        result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        
        print(f"Template matching max correlation: {max_val:.4f} at {max_loc}")
        
        if max_val > 0.8:
            match_x, match_y = max_loc
            print(f"Match found at: x={match_x}, y={match_y}")
            # Save the captured region that matched
            matched_crop = screenshot[match_y:match_y+th, match_x:match_x+tw]
            cv2.imwrite('resources/captured_match.png', matched_crop)
            print("Saved resources/captured_match.png")
        else:
            print("Template match confidence too low.")

if __name__ == '__main__':
    test_capture_and_match()
