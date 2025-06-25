from __future__ import annotations
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from typing import Union, Optional
from os import PathLike
import numpy as np
import os
import time
import logging
import json
import socket
from datetime import datetime
from pathlib import Path
import platform
import re

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create separate logger for API calls
api_logger = logging.getLogger('api_calls')
api_handler = logging.FileHandler('api_calls.log')
api_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
api_logger.addHandler(api_handler)
api_logger.setLevel(logging.INFO)

def read_y4m_frames(y4m_path: Union[str, PathLike], max_frames: Optional[int] = None) -> list[np.ndarray]:
    """Read Y4M video file without FFmpeg dependency."""
    y4m_path = Path(y4m_path)
    if not y4m_path.exists():
        raise FileNotFoundError(f"Y4M file not found: {y4m_path}")

    frames = []
    with open(y4m_path, 'rb') as f:
        header = f.readline().decode('ascii').strip()
        match = re.search(r'W(\d+) H(\d+)', header)
        if not match:
            raise ValueError("Invalid Y4M header (missing width/height)")
        
        width, height = int(match.group(1)), int(match.group(2))
        frame_size = width * height * 3 // 2

        while True:
            frame_header = f.readline()
            if not frame_header:
                break
            
            yuv_data = f.read(frame_size)
            if not yuv_data:
                break
            
            yuv_array = np.frombuffer(yuv_data, dtype=np.uint8)
            frames.append(yuv_array)
            
            if max_frames and len(frames) >= max_frames:
                break

    return frames

def verify_media_files(video_path, audio_path):
    """Verify that media files exist and are accessible"""
    video_path = Path(video_path).resolve()
    audio_path = Path(audio_path).resolve()
    
    logger.info(f"Checking video file: {video_path}")
    if not video_path.exists():
        logger.error(f"Video file not found: {video_path}")
        return False, None
    
    logger.info(f"Checking audio file: {audio_path}")
    if not audio_path.exists():
        logger.warning(f"Audio file not found: {audio_path}")
        audio_path = None
    
    try:
        frames = read_y4m_frames(video_path, max_frames=1)
        if frames:
            logger.info(f"Y4M file verified: {len(frames)} frame(s) read successfully")
            logger.info(f"Frame shape: {frames[0].shape}")
        else:
            logger.error("Y4M file contains no frames")
            return False, None
    except Exception as e:
        logger.error(f"Y4M file verification failed: {e}")
        return False, None
    
    return True, audio_path
