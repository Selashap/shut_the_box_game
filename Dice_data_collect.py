import cv2
import time
import os

# Open the camera
cap = cv2.VideoCapture(1)

# Create folders for each dice value (1-6)
base_path = "dice_images"
for i in range(1, 7):
    os.makedirs(os.path.join(base_path, f"dice_{i}"), exist_ok=True)

print("Press a key (1-6) to capture an image of that dice number.")
print("Press 'q' to quit.")

while True:
    # Capture frame-by-frame
    ret, frame = cap.read()
    if not ret:
        print("Failed to capture image.")
        break

    # Display the live frame
    cv2.imshow("Dice Capture", frame)

    # Wait for a key press
    key = cv2.waitKey(1) & 0xFF

    # Check if key is a number (1-6)
    if key in [ord(str(i)) for i in range(1, 7)]:
        dice_value = chr(key) 
        folder_path = os.path.join(base_path, f"dice_{dice_value}")  # Folder for that dice number
        timestamp = int(time.time())  # Unique timestamp
        file_name = os.path.join(folder_path, f"{timestamp}.jpg")

        # Save the image
        cv2.imwrite(file_name, frame)
        print(f"Saved: {file_name}")

    # Quit when 'q' is pressed
    if key == ord('q'):
        print("Exiting...")
        break

# Release resources
cap.release()
cv2.destroyAllWindows()