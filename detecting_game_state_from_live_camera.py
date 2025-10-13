import cv2
import itertools
from ultralytics import YOLO
import numpy as np

def get_yolo_info(results, model_type, box_coords):
    open_values = []
    closed_values = []
    values = []
    colors = []
    coords = []
    model_names = results[0].names if results else []

    for result in results:
        if result.boxes:
            boxes = result.boxes.xyxy.cpu().numpy().astype(int)
            classes = result.boxes.cls.cpu().numpy().astype(int)
            for i, (x1, y1, x2, y2) in enumerate(boxes):
                class_id = classes[i]
                label = model_names[class_id] if class_id < len(model_names) else str(class_id)
                try:
                    if model_type == 'box':
                        if "-" in label:
                            box_num = int(label.split("-")[0])
                            box_coords[box_num] = (x1, y1, x2, y2)
                            if "open" in label:
                                open_values.append(box_num)
                            elif "closed" in label:
                                closed_values.append(box_num)
                    elif model_type == 'dice':
                        val = int(label)
                        values.append(val)
                        coords.append((x1, y1, x2, y2))
                        colors.append((255, 0, 0))
                except ValueError:
                    print(f"Invalid label '{label}'")

    if model_type == 'box':
        return open_values, closed_values, colors, box_coords
    elif model_type == 'dice':
        return values, colors, coords, box_coords

def solve_shut_the_box(dice_values, open_boxes):
    dice_sum = sum(dice_values)
    possible_combinations = []
    for i in range(1, len(open_boxes) + 1):
        for combo in itertools.combinations(open_boxes, i):
            if sum(combo) == dice_sum:
                possible_combinations.append(list(combo))
    return possible_combinations

def overlay_game_info(frame, dice_values, possible_combinations, box_coords, open_boxes):
    font = cv2.FONT_HERSHEY_SIMPLEX
    text_color = (0, 0, 0)
    text_size = 0.6
    text_thickness = 2
    y_offset = 10
    y_increment = 30

    info_texts = [f"Dice: {dice_values}", "Open Boxes: " + ", ".join(map(str, sorted(open_boxes)))]

    if possible_combinations:
        info_texts.append("Possible to close: " + ", ".join(str(combo) for combo in possible_combinations))
    else:
        info_texts.append("No possible combinations")

    # Bottom-left positioning based on frame size
    h, w, _ = frame.shape
    x_pos = 10
    y_start = h - (len(info_texts) * y_increment) - 10

    for i, line in enumerate(info_texts):
        y = y_start + i * y_increment
        cv2.putText(frame, line, (x_pos, y), font, text_size, text_color, text_thickness)

    return frame

def main():
    box_model = YOLO("Box_Yolo_model.pt")
    dice_model = YOLO("Dice_Yolo_model.pt")

    cap = cv2.VideoCapture(1)
    if not cap.isOpened():
        print("Error: Could not open camera.")
        return
    #screen for live camera
    cv2.namedWindow("Shut the Box - Live", cv2.WINDOW_NORMAL)
    box_coords = {}

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Could not read frame from camera.")
            break

        box_results = box_model.predict(frame, conf=0.4)
        dice_results = dice_model.predict(frame, conf=0.4)

        frame_with_boxes = box_results[0].plot()
        frame_with_dice = dice_results[0].plot()
        combined_frame = cv2.addWeighted(frame_with_boxes, 0.7, frame_with_dice, 0.7, 0)  # slightly dimmed

        open_boxes, closed_boxes, _, box_coords = get_yolo_info(box_results, 'box', box_coords)
        dice_values, _, _, _ = get_yolo_info(dice_results, 'dice', {})

        dice_values = dice_values[:2]

        possible_combinations = solve_shut_the_box(dice_values, open_boxes)
        final_frame = overlay_game_info(combined_frame, dice_values, possible_combinations, box_coords, open_boxes)

        cv2.imshow("Shut the Box - Live", final_frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()

