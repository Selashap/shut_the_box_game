import tkinter as tk
from tkinter import ttk, filedialog
from PIL import Image, ImageTk
import subprocess
import threading

def show_image_and_result(image_path, result_text, image_label, result_label):
    try:
        img = Image.open(image_path)
        img = img.resize((400, 300))
        img_tk = ImageTk.PhotoImage(img)

        # Update the image_label with the new image
        image_label.config(image=img_tk)
        image_label.image = img_tk

        # Update the result label with the result text
        result_label.config(text=result_text)

    except Exception as e:
        print(f"Error: {e}")
        image_label.config(image=None)
        result_label.config(text=f"Error: {e}", foreground="red")

def create_image_selection_frame(root, image_label, result_label):
    image_frame = ttk.Frame(root, padding="10")
    ttk.Label(image_frame, text="Select Image:").pack(pady=5)

    def browse_image():
        image_path = filedialog.askopenfilename(
            title="Browse for an image",
            filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.gif")],  # Added gif
        )
        if image_path:
            # Start the image processing in a separate thread to keep the GUI responsive
            threading.Thread(target=run_image_detection, args=(image_path, image_label, result_label)).start()

    browse_button = ttk.Button(
        image_frame,
        text="Browse for an image",
        command=browse_image,
    )
    browse_button.pack(pady=10)
    return image_frame

def create_live_camera_frame(root):
    camera_frame = ttk.Frame(root, padding="10")
    ttk.Label(camera_frame, text="Live Camera Feed:").pack(pady=5)
    camera_button = ttk.Button(
        camera_frame,
        text="Start Live Camera Detection",
        command=lambda: threading.Thread(target=run_live_camera_detection).start(),  # Start in a thread
    )
    camera_button.pack(pady=5)
    return camera_frame

def run_image_detection(image_path, image_label, result_label):
    try:
        process = subprocess.Popen(
            ["python", "detecting_game_state_from_images.py", image_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = process.communicate()

        if stderr:
            error_message = stderr.decode("utf-8")
            print(f"Error: {error_message}")
            # Use root.after to update the GUI from the thread
            root.after(0, show_image_and_result, image_path, f"Error: {error_message}", image_label, result_label)
            return

        result_text = stdout.decode("utf-8").strip()
        print(f"Result: {result_text}")
        # Use root.after to update the GUI from the thread
        root.after(0, show_image_and_result, image_path, result_text, image_label, result_label)

    except Exception as e:
        print(f"Error: {e}")
        root.after(0, show_image_and_result, image_path, f"Error: {e}", image_label, result_label)

def run_live_camera_detection():

    try:
        process = subprocess.Popen(
            ["python", "detecting_game_state_from_live_camera.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = process.communicate()

        if stderr:
            error_message = stderr.decode("utf-8")
            print(f"Error: {error_message}")
            return

        result_text = stdout.decode("utf-8").strip()
        print(f"Result: {result_text}")

    except Exception as e:
        print(f"Error: {e}")

def main():
    global root  # Declare root as global
    root = tk.Tk()
    root.title("Game State Detection")
    root.geometry("600x400")

    notebook = ttk.Notebook(root)

    image_label = tk.Label(notebook)
    result_label = tk.Label(notebook, text="Result will be displayed here.")
    image_frame = create_image_selection_frame(notebook, image_label, result_label)
    camera_frame = create_live_camera_frame(notebook)

    notebook.add(image_frame, text="Detect from Image")
    notebook.add(camera_frame, text="Detect from Live Camera")
    notebook.pack(expand=True, fill="both")

    image_label.pack(pady=10)
    result_label.pack(pady=10)

    root.mainloop()

if __name__ == "__main__":
    main()
