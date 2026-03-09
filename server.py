# Simple server untuk menerima stream
import socket
import pickle
import struct
import cv2
import numpy as np

HOST = "10.94.149.28"
PORT = 4444
BUFFER_SIZE = 4096
MAX_FRAME_SIZE = 10 * 1024 * 1024  # 10MB limit

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((HOST, PORT))
s.listen(5)

print(f"[+] Listening on {HOST}:{PORT}")

conn, addr = s.accept()
print(f"[+] Connection from {addr}")

data = b""
payload_size = struct.calcsize("Q")

while True:
    try:

        # Ambil ukuran frame
        while len(data) < payload_size:
            packet = conn.recv(BUFFER_SIZE)
            if not packet:
                raise ConnectionError("Client disconnected")
            data += packet

        packed_msg_size = data[:payload_size]
        data = data[payload_size:]
        msg_size = struct.unpack("Q", packed_msg_size)[0]

        # Proteksi ukuran frame (anti DoS)
        if msg_size > MAX_FRAME_SIZE:
            print("[-] Frame terlalu besar, kemungkinan attack")
            break

        # Ambil data frame sesuai ukuran
        while len(data) < msg_size:
            packet = conn.recv(BUFFER_SIZE)
            if not packet:
                raise ConnectionError("Client disconnected")
            data += packet

        frame_data = data[:msg_size]
        data = data[msg_size:]

        # Decode frame
        frame_pickle = pickle.loads(frame_data)
        frame = cv2.imdecode(
            np.frombuffer(frame_pickle, np.uint8),
            cv2.IMREAD_COLOR
        )

        cv2.imshow("Screen Stream", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    except Exception as e:
        print(f"[!] Error: {e}")
        break

cv2.destroyAllWindows()
conn.close()
s.close()