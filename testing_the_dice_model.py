from ultralytics import YOLO

model = YOLO('Dice_Yolo_model.pt')

results = model(source=1, show=True, conf=0.4, save=True)
