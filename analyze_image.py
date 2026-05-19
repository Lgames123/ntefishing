import cv2
import numpy as np

def analyze():
    # Load the image
    img = cv2.imread('resources/fishing.png')
    if img is None:
        print("Failed to load resources/fishing.png")
        return
        
    h, w, c = img.shape
    print(f"Loaded resources/fishing.png: {w}x{h} (channels: {c})")
    
    # Convert to HSV
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # Let's inspect some color ranges.
    # We can try to define broad masks first.
    # Yellow is typically around H=20-35, S=100-255, V=100-255
    # Green is typically around H=35-85, S=50-255, V=50-255
    
    # Let's print out what colors we find in the image.
    # We can check a grid or find the dominant colors.
    # Let's save a visualization with different color thresholds.
    
    # Yellow Mask
    lower_yellow = np.array([15, 100, 100])
    upper_yellow = np.array([35, 255, 255])
    yellow_mask = cv2.inRange(hsv, lower_yellow, upper_yellow)
    
    # Green Mask
    # Note: the green bar might be a bit cyan or dark. Let's try H from 35 to 90.
    lower_green = np.array([35, 80, 80])
    upper_green = np.array([90, 255, 255])
    green_mask = cv2.inRange(hsv, lower_green, upper_green)
    
    # Find contours
    yellow_contours, _ = cv2.findContours(yellow_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    green_contours, _ = cv2.findContours(green_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    print(f"Found {len(yellow_contours)} yellow contours")
    for i, cnt in enumerate(yellow_contours):
        x, y, w_cnt, h_cnt = cv2.boundingRect(cnt)
        print(f"  Yellow {i}: x={x}, y={y}, w={w_cnt}, h={h_cnt}, area={cv2.contourArea(cnt)}")
        
    print(f"Found {len(green_contours)} green contours")
    for i, cnt in enumerate(green_contours):
        x, y, w_cnt, h_cnt = cv2.boundingRect(cnt)
        print(f"  Green {i}: x={x}, y={y}, w={w_cnt}, h={h_cnt}, area={cv2.contourArea(cnt)}")

    # Let's save the masks and original image with bounding boxes drawn
    vis = img.copy()
    for cnt in yellow_contours:
        if cv2.contourArea(cnt) > 5:
            x, y, w_cnt, h_cnt = cv2.boundingRect(cnt)
            cv2.rectangle(vis, (x, y), (x+w_cnt, y+h_cnt), (0, 0, 255), 2) # Draw Red for yellow
            cv2.putText(vis, "Yellow", (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
            
    for cnt in green_contours:
        if cv2.contourArea(cnt) > 20:
            x, y, w_cnt, h_cnt = cv2.boundingRect(cnt)
            cv2.rectangle(vis, (x, y), (x+w_cnt, y+h_cnt), (0, 255, 0), 2) # Draw Green
            cv2.putText(vis, "Green", (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            
    cv2.imwrite('resources/analysis_result.png', vis)
    cv2.imwrite('resources/yellow_mask.png', yellow_mask)
    cv2.imwrite('resources/green_mask.png', green_mask)
    print("Saved analysis_result.png, yellow_mask.png, green_mask.png in resources directory.")

if __name__ == '__main__':
    analyze()
