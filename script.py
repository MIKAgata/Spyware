#!/usr/bin/env python3

import socket
import cv2
import numpy as np
import struct
import time
import os
import signal
from PIL import ImageGrab
from dotenv import load_dotenv
import logging
from dataclasses import dataclass
from typing import Optional

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

logger = logging.getLogger(__name__)


@dataclass
class Config:
    server_ip: str = os.getenv("SERVER_IP", "127.0.0.1")
    server_port: int = int(os.getenv("SERVER_PORT", "4444"))
    quality: int = int(os.getenv("QUALITY", "40"))
    max_fps: int = int(os.getenv("MAX_FPS", "8"))
    reconnect_delay: int = 5
    screen_region: Optional[tuple] = None


class ScreenStreamer:

    def __init__(self, config: Config):

        self.config = config
        self.socket = None
        self.running = True

        self.frame_interval = 1.0 / config.max_fps
        self.last_frame = 0

        self.encode_params = [cv2.IMWRITE_JPEG_QUALITY, config.quality]

        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGTERM, self.stop)

    def stop(self, *args):
        logger.info("Stopping streamer...")
        self.running = False

        if self.socket:
            try:
                self.socket.close()
            except:
                pass

    def connect(self):

        while self.running:

            try:
                logger.info(f"Connecting to {self.config.server_ip}:{self.config.server_port}")

                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(10)

                s.connect((self.config.server_ip, self.config.server_port))

                s.settimeout(None)

                self.socket = s

                logger.info("Connected")

                return True

            except Exception as e:

                logger.warning(f"Connection failed: {e}")

                time.sleep(self.config.reconnect_delay)

        return False

    def capture_screen(self):

        try:

            bbox = self.config.screen_region

            screenshot = ImageGrab.grab(bbox=bbox)

            frame = np.array(screenshot)

            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

            h, w = frame.shape[:2]

            if max(h, w) > 1280:

                scale = 1280 / max(h, w)

                frame = cv2.resize(
                    frame,
                    (int(w * scale), int(h * scale)),
                    interpolation=cv2.INTER_AREA
                )

            return frame

        except Exception as e:

            logger.error(f"Capture error: {e}")

            return None

    def send_frame(self, frame):

        try:

            result, encoded = cv2.imencode(".jpg", frame, self.encode_params)

            if not result:
                return False

            data = encoded.tobytes()

            size = struct.pack("Q", len(data))

            self.socket.sendall(size + data)

            return True

        except Exception as e:

            logger.warning(f"Send failed: {e}")

            return False

    def stream(self):

        logger.info("Streaming started")

        frame_count = 0
        start_time = time.time()

        while self.running:

            now = time.time()

            if now - self.last_frame < self.frame_interval:
                time.sleep(0.001)
                continue

            self.last_frame = now

            frame = self.capture_screen()

            if frame is None:
                continue

            if not self.send_frame(frame):
                break

            frame_count += 1

            if frame_count % (self.config.max_fps * 5) == 0:

                elapsed = time.time() - start_time
                fps = frame_count / elapsed

                logger.info(f"Streaming {fps:.2f} FPS")

        logger.warning("Streaming stopped")

    def run(self):

        logger.info("Screen Streamer Started")

        while self.running:

            if not self.connect():
                break

            try:

                self.stream()

            finally:

                if self.socket:
                    try:
                        self.socket.close()
                    except:
                        pass

                logger.info(f"Reconnecting in {self.config.reconnect_delay}s")

                time.sleep(self.config.reconnect_delay)


def main():

    config = Config()

    if not config.server_ip:
        logger.error("SERVER_IP not set")
        return

    streamer = ScreenStreamer(config)

    streamer.run()


if __name__ == "__main__":
    main()