# server_receiver.py (Jalankan di laptop ANDA)
import socket
import cv2
import numpy as np
import struct
import pickle
import os

SERVER_IP = os.getenv("SERVER_IP")
SERVER_PORT = os.getenv("SERVER_PORT")

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((SERVER_IP, SERVER_PORT))
server_socket.listen(1)
print(f"[*] Server mendengarkan di {SERVER_IP}:{SERVER_PORT}")

client_socket, addr = server_socket.accept()
print(f"[+] Koneksi diterima dari {addr}")

data = b""
payload_size = struct.calcsize("Q") 

while True:

    while len(data) < payload_size:
        packet = client_socket.recv(4*1024) 
        if not packet:
            break
        data += packet
    if not data:
        break

    packed_msg_size = data[:payload_size]
    data = data[payload_size:]
    msg_size = struct.unpack("Q", packed_msg_size)[0]

    while len(data) < msg_size:
        data += client_socket.recv(4*1024)
    if not data:
        break

    frame_data = data[:msg_size]
    data = data[msg_size:]

    frame = pickle.loads(frame_data)
    frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)

    cv2.imshow('Menerima Streaming dari Teman', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

client_socket.close()
server_socket.close()
cv2.destroyAllWindows()