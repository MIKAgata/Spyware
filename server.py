import socket
import cv2
import struct
import pickle
import os
from dotenv import load_dotenv

load_dotenv()

SERVER_IP = os.getenv("SERVER_IP", " 10.94.149.28")
SERVER_PORT = int(os.getenv("SERVER_PORT", 9999))

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

server_socket.bind((SERVER_IP, SERVER_PORT))
server_socket.listen(1)

print(f"[*] Server listening on {SERVER_IP}:{SERVER_PORT}")

client_socket = None

try:
    client_socket, addr = server_socket.accept()
    print(f"[+] Connection from {addr}")

    data = b""
    payload_size = struct.calcsize("Q")

    while True:

        while len(data) < payload_size:
            packet = client_socket.recv(4096)
            if not packet:
                raise ConnectionError("Client disconnected")
            data += packet

        packed_msg_size = data[:payload_size]
        data = data[payload_size:]

        msg_size = struct.unpack("Q", packed_msg_size)[0]

        while len(data) < msg_size:
            packet = client_socket.recv(4096)
            if not packet:
                raise ConnectionError("Client disconnected")
            data += packet

        frame_data = data[:msg_size]
        data = data[msg_size:]

        try:
            frame = pickle.loads(frame_data)
            frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)
        except Exception:
            print("[!] Frame decode error")
            continue

        if frame is None:
            continue

        cv2.imshow("Screen Stream", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

except KeyboardInterrupt:
    print("\n[!] Interrupted by user")

except Exception as e:
    print(f"[!] Error: {e}")

finally:
    print("[*] Cleaning up...")

    if client_socket:
        client_socket.close()

    server_socket.close()
    cv2.destroyAllWindows()