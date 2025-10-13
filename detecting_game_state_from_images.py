import cv2
import itertools
from ultralytics import YOLO
import tkinter as tk
from tkinter import filedialog
import numpy as np

def main(image_path):
    box_model = YOLO("Box_Yolo_model.pt")
    dice_model = YOLO("Dice_Yolo_model.pt")

    image = cv2.imread(image_path)
    if image is None:
        print(f"Error: Could not read image from {image_path}")
        return

    processed_image = process_image(image, box_model, dice_model)
    return processed_image

def process_image(image, box_model, dice_model):
    box_coords = {}

    # Run YOLO detections
    box_results = box_model.predict(image)
    dice_results = dice_model.predict(image)

    box_image = box_results[0].plot()
    dice_image = dice_results[0].plot()

    overlay = cv2.addWeighted(box_image, 0.5, dice_image, 0.5, 0)

    combined_image = cv2.addWeighted(image, 0.5, overlay, 0.5, 0)

    open_boxes, dice_values, dice_colors, box_coords, box_colors, box_labels = get_yolo_results(
        image, box_model, dice_model, box_coords
    )
    possible_combinations = solve_shut_the_box(dice_values, open_boxes)

    # Overlay game information
    processed_image = display_results(combined_image, dice_values, open_boxes,
                                      possible_combinations, box_coords)
    return processed_image

def get_yolo_results(image, box_model, dice_model, box_coords):
    box_results = box_model.predict(image)
    open_boxes = []
    closed_boxes = []
    box_colors = {}
    box_labels = {}

    for result in box_results:
        if result.boxes:
            boxes = result.boxes.xyxy.cpu().numpy().astype(int)
            classes = result.boxes.cls.cpu().numpy().astype(int)
            names = result.names

            for i, (x1, y1, x2, y2) in enumerate(boxes):
                class_id = classes[i]
                if class_id < len(names):
                    label = names[class_id]
                    color = (0, 255, 0)
                    if "-" in label:
                        try:
                            box_number = int(label.split("-")[0])
                            if "open" in label:
                                open_boxes.append(box_number)
                                box_coords[box_number] = (x1, y1, x2, y2)
                                box_colors[box_number] = color
                                box_labels[box_number] = label
                            elif "closed" in label:
                                closed_boxes.append(box_number)
                                box_coords[box_number] = (x1, y1, x2, y2)
                                box_colors[box_number] = color
                                box_labels[box_number] = label
                        except ValueError:
                            print(f"Warning: Could not extract box number from label '{label}'.")
                    else:
                        print(f"Warning: Box label '{label}' is not in 'X-open' or 'X-closed' format.")
                else:
                    print(f"Warning: Class ID {class_id} is out of range for box_model.names.")

    if not open_boxes and not closed_boxes:
        open_boxes = list(range(1, 10))
        for i in range(1, 10):
            box_colors[i] = (0, 255, 0)
            box_labels[i] = f"{i}-open"

    # Dice detection
    dice_results = dice_model.predict(image)
    dice_values = []
    dice_colors = []
    for result in dice_results:
        if result.boxes:
            boxes = result.boxes.xyxy.cpu().numpy().astype(int)
            classes = result.boxes.cls.cpu().numpy().astype(int)
            names = result.names
            for i, (x1, y1, x2, y2) in enumerate(boxes):
                class_id = classes[i]
                if class_id < len(dice_model.names):
                    label = names[class_id]
                    try:
                        dice_value = int(label)
                        dice_values.append(dice_value)
                        color = (255, 0, 0)
                        dice_colors.append(color)
                    except ValueError:
                        print(f"Warning: Dice label '{label}' is not a valid number. Label is: {label}")
                else:
                    print(f"Warning: Class ID {class_id} is out of range for dice_model.names.")
    dice_values = dice_values[:2]
    dice_colors = dice_colors[:2]

    return open_boxes, dice_values, dice_colors, box_coords, box_colors, box_labels

def solve_shut_the_box(dice_values, open_boxes):
    dice_sum = sum(dice_values)
    possible_combinations = []

    for i in range(1, len(open_boxes) + 1):
        for combo in itertools.combinations(open_boxes, i):
            if sum(combo) == dice_sum:
                possible_combinations.append(list(combo))

    return possible_combinations

def display_results(image, dice_values, open_boxes, possible_combinations, box_coords):
    font = cv2.FONT_HERSHEY_SIMPLEX
    text_color = (0, 0, 0)
    text_size = 0.6
    text_thickness = 2
    line_spacing = 25

    max_height = 800
    max_width = 1000
    h, w = image.shape[:2]
    if h > max_height or w > max_width:
        scaling_factor = min(max_width / w, max_height / h)
        image = cv2.resize(image, None, fx=scaling_factor, fy=scaling_factor)

    # Prepare lines of text
    info_lines = [
        f"Dice: {dice_values}",
        "Open Boxes: " + ', '.join(map(str, sorted(open_boxes))),
        "Possible to close: " + ', '.join(str(combo) for combo in possible_combinations)
        if possible_combinations else "No possible combinations"
    ]

    # Start from bottom-left
    y_start = image.shape[0] - 10 - (len(info_lines) - 1) * line_spacing

    for i, text in enumerate(info_lines):
        position = (10, y_start + i * line_spacing)
        cv2.putText(image, text, position, font, text_size, text_color, text_thickness)

    return image

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(
        title="Select Image",
        filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.gif")],
    )
    if file_path:
        processed_image = main(file_path)
        cv2.imshow("Shut the Box - Solution", processed_image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    else:
        print("No image selected. Exiting.")
