import cv2
import numpy as np

def test_detection():
    # Load reference image
    img = cv2.imread('resources/fishing.png')
    if img is None:
        print("Failed to load resources/fishing.png")
        return
        
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # Masks
    lower_yellow = np.array([15, 80, 80])
    upper_yellow = np.array([35, 255, 255])
    yellow_mask = cv2.inRange(hsv, lower_yellow, upper_yellow)
    
    lower_green = np.array([35, 50, 50])
    upper_green = np.array([90, 255, 255])
    green_mask = cv2.inRange(hsv, lower_green, upper_green)
    
    # Contours
    yellow_contours, _ = cv2.findContours(yellow_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    green_contours, _ = cv2.findContours(green_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Find Yellow Marker
    yellow_marker = None
    for cnt in yellow_contours:
        x, y, w, h = cv2.boundingRect(cnt)
        aspect_ratio = h / float(w)
        area = cv2.contourArea(cnt)
        # Filters: vertical aspect ratio, small width, and small area
        if aspect_ratio > 1.5 and w < 20 and 50 < area < 500:
            yellow_marker = (x, y, w, h)
            break
            
    # Find Green Rectangle
    green_rect = None
    max_green_area = -1
    for cnt in green_contours:
        x, y, w, h = cv2.boundingRect(cnt)
        aspect_ratio = w / float(h)
        area = cv2.contourArea(cnt)
        # Filters: horizontal aspect ratio, large width, and largest area
        if aspect_ratio > 2.0 and w > 50 and area > 500:
            if area > max_green_area:
                max_green_area = area
                green_rect = (x, y, w, h)
                
    print("Detection Results:")
    if yellow_marker:
        x, y, w, h = yellow_marker
        print(f"  Yellow Marker detected at: x={x}, y={y}, w={w}, h={h} (center={x + w/2:.1f})")
    else:
        print("  Yellow Marker NOT detected!")
        
    if green_rect:
        x, y, w, h = green_rect
        print(f"  Green Rectangle detected at: x={x}, y={y}, w={w}, h={h} (range=[{x}, {x+w}])")
    else:
        print("  Green Rectangle NOT detected!")
        
    if yellow_marker and green_rect:
        yx = yellow_marker[0] + yellow_marker[2]/2.0
        gx_left = green_rect[0]
        gx_right = green_rect[0] + green_rect[2]
        
        # Decide action
        margin = 5 # small margin
        if yx < gx_left + margin:
            action = "PULL RIGHT (Press D)"
        elif yx > gx_right - margin:
            action = "PULL LEFT (Press A)"
        else:
            action = "STAY (Release A and D)"
            
        print(f"  Decided Action: {action}")

if __name__ == '__main__':
    test_detection()
