"""
Configuration module for Hand-Movement-Detected-Working-Mouse.
Customizable parameters for camera, gestures, smoothing, and display HUD.
"""

from dataclasses import dataclass
from typing import Tuple


@dataclass
class AppConfig:
    # --- Camera & Capture Settings ---
    CAMERA_INDEX: int = 0
    CAMERA_WIDTH: int = 640
    CAMERA_HEIGHT: int = 480
    FLIP_HORIZONTAL: bool = True  # Mirror camera feed so movements feel natural
    TARGET_FPS: int = 60

    # --- Active Tracking Area (Screen Mapping Margin) ---
    # Margin in pixels from frame border inside which coordinates map to full screen.
    # Prevents user having to reach to the extreme camera edges to reach screen corners.
    FRAME_MARGIN_X: int = 90
    FRAME_MARGIN_Y: int = 70

    # --- Mouse Movement & Smoothing ---
    # Smoothing factor: higher = smoother cursor, lower = faster raw response.
    # 5-7 gives an ideal balance of jitter elimination and quick responsiveness.
    SMOOTHING_FACTOR: float = 5.0
    ACCELERATION_FACTOR: float = 1.2  # Slight velocity-based acceleration

    # Normalized pinch distance threshold (distance relative to hand landmark reference scale)
    PINCH_THRESHOLD: float = 0.085
    PINCH_RELEASE_THRESHOLD: float = 0.10

    # Hold timing: Holding pinch for >= HOLD_DELAY_SECONDS engages mouse hold/drag
    HOLD_DELAY_SECONDS: float = 2.0
    
    # Minimum pinch duration required to count as a click (filters out 1-frame tracking blips)
    MIN_CLICK_DURATION: float = 0.06
    
    # Maximum pinch duration to register as a single click upon release
    MAX_CLICK_DURATION: float = 1.95

    # Secondary gestures
    RIGHT_CLICK_ENABLED: bool = True
    RIGHT_PINCH_THRESHOLD: float = 0.065  # Middle finger tip to thumb tip

    SCROLL_ENABLED: bool = True
    SCROLL_DISTANCE_THRESHOLD: float = 0.065  # Index and middle finger close together
    SCROLL_SPEED_MULTIPLIER: int = 15

    # --- UI & Visual HUD Themes (BGR format for OpenCV) ---
    COLOR_PRIMARY_CYAN: Tuple[int, int, int] = (255, 220, 0)      # High-tech cyan
    COLOR_SUCCESS_GREEN: Tuple[int, int, int] = (70, 220, 100)    # Active emerald
    COLOR_HOLD_ORANGE: Tuple[int, int, int] = (0, 140, 255)       # Amber/orange during 2s hold
    COLOR_CLICK_FLASH: Tuple[int, int, int] = (255, 255, 255)     # White flash on click
    COLOR_HUD_BG: Tuple[int, int, int] = (20, 20, 25)             # Dark glassmorphism card
    COLOR_TEXT: Tuple[int, int, int] = (240, 240, 240)            # Crisp white text
    COLOR_ACCENT_PURPLE: Tuple[int, int, int] = (230, 80, 180)    # Modern accent

    # Display flags
    SHOW_HUD: bool = True
    SHOW_LANDMARKS: bool = True
    SHOW_TRACKING_BOX: bool = True
    WINDOW_TITLE: str = "Virtual Hand Mouse Pro"

    # PyAutoGUI Safety settings
    FAILSAFE_ACTIVE: bool = False  # Disabled to prevent edge crashes; custom clamping used


# Global default configuration instance
DEFAULT_CONFIG = AppConfig()
