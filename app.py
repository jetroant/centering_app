import os
import sys
import glob
import base64
import time
import threading
import subprocess
from flask import Flask, render_template, jsonify, request, send_from_directory

app = Flask(__name__)

# Define our local folders
# Adjust BASE_DIR to work correctly with PyInstaller
if getattr(sys, 'frozen', False):
    # If the application is run as a bundle, the PyInstaller bootloader
    # extends the sys module by a flag frozen=True and sets the app 
    # path into variable _MEIPASS'.
    # For onefile build, the executable path is sys.executable.
    BASE_DIR = os.path.dirname(sys.executable)
    template_dir = os.path.join(sys._MEIPASS, 'templates')
    app.template_folder = template_dir
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SCANS_DIR = os.path.join(BASE_DIR, "scans")
EXPORTS_DIR = os.path.join(BASE_DIR, "exports")

# Ensure folders exist
os.makedirs(SCANS_DIR, exist_ok=True)
os.makedirs(EXPORTS_DIR, exist_ok=True)

@app.route("/")
def index():
    return render_template("index.html")

# Serve raw images so the UI can display them
@app.route('/scans/<path:filename>')
def serve_scans(filename):
    return send_from_directory(SCANS_DIR, filename)

@app.route("/get_defaults", methods=["GET"])
def get_defaults():
    """Finds the newest front and back images based on user logic."""
    files = glob.glob(os.path.join(SCANS_DIR, "*.*"))
    # Sort files by modification time (newest first)
    files.sort(key=os.path.getmtime, reverse=True)
    
    front_img = None
    back_img = None
    
    for f in files:
        fname = os.path.basename(f).lower()
        # Only accept standard image formats
        if not fname.endswith(('.png', '.jpg', '.jpeg', '.webp')):
            continue
            
        if 'back' in fname and not back_img:
            back_img = os.path.basename(f)
        elif 'back' not in fname and not front_img:
            front_img = os.path.basename(f)
            
        if front_img and back_img:
            break
            
    return jsonify({
        "front": f"/scans/{front_img}" if front_img else None,
        "back": f"/scans/{back_img}" if back_img else None,
        "front_filename": front_img
    })

@app.route("/save_export", methods=["POST"])
def save_export():
    """Saves the flattened image with the printed text."""
    data = request.json
    image_data = data.get("image_base64")
    original_name = data.get("original_name", "manual_card")
    
    if image_data:
        try:
            header, encoded = image_data.split(",", 1)
            image_bytes = base64.b64decode(encoded)
            
            # Create a clean save name (e.g., card_centered_162345.jpg)
            base_name = os.path.splitext(original_name)[0]
            timestamp = str(int(time.time()))[-5:]
            save_name = f"{base_name}_centered_{timestamp}.jpg"
            
            save_path = os.path.join(EXPORTS_DIR, save_name)
            with open(save_path, "wb") as f:
                f.write(image_bytes)
            return jsonify({"success": True, "saved_as": save_name})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)})
            
    return jsonify({"success": False, "error": "No image data provided"})

def open_browser():
    time.sleep(1.5)
    try:
        subprocess.run(['open', '-a', 'Safari', 'http://127.0.0.1:5050'])
    except Exception as e:
        print(f"Could not open Safari: {e}")

if __name__ == "__main__":
    threading.Thread(target=open_browser, daemon=True).start()
    app.run(debug=False, port=5050)