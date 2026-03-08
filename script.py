import socket
import cv2
import numpy as np
import pickle
import struct
from PIL import ImageGrab
from dotenv import load_dotenv
import os

load_dotenv()
SERVER_IP = os.getenv("SERVER_IP")
SERVER_PORT = int(os.getenv("SERVER_PORT"))

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((SERVER_IP, SERVER_PORT))
print(f"[*] Terhubung ke server {SERVER_IP}:{SERVER_PORT}")

try:
    while True:
        screenshot = ImageGrab.grab()
        frame = np.array(screenshot)
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        result, frame_encode = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
        data = pickle.dumps(frame_encode)
        message_size = struct.pack("Q", len(data))
        client_socket.sendall(message_size + data)

except Exception as e:
    print(f"Error: {e}")
finally:
    client_socket.close()