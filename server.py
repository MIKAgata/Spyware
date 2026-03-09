# Simple server untuk menerima stream
import socket
import pickle
import struct
import cv2
import numpy as np

s = socket.socket()
s.bind(('10.94.149.28', 4444))
s.listen(1)
conn, addr = s.accept()

while True:
    data = b""
    payload_size = struct.calcsize("Q")
    
    while len(data) < payload_size:
        data += conn.recv(4096)
    
    packed_msg_size = data[:payload_size]
    data = data[payload_size:]
    msg_size = struct.unpack("=Q", packed_msg_size)[0]
    
    while len(data) < msg_size:
        data += conn.recv(4096)
    
    frame_data = pickle.loads(data)
    frame = cv2.imdecode(np.frombuffer(frame_data, np.uint8), cv2.IMREAD_COLOR)
    cv2.imshow('Screen Stream', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()
conn.close()