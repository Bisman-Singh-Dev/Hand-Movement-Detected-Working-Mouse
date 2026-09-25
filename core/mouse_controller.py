"""
Mouse Controller Module.
Handles smooth coordinate transformation, boundary damping, acceleration curves,
and robust left/right click, hold, drag, and scroll operations.
"""

import math
from typing import Tuple
import pyautogui

# Safety: Disable PyAutoGUI's automatic abort fail-safe at (0, 0)
# We handle screen clamping within safe virtual bounds [2, screen_width - 2].
pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.001  # Ultra-low internal pause for smooth 60fps tracking


class MouseController:
    def __init__(
        self,
        smoothing: float = 5.0,
        margin_x: int = 80,
        margin_y: int = 60,
        cam_w: int = 640,
        cam_h: int = 480,
    ):
        self.screen_w, self.screen_h = pyautogui.size()
        self.smoothing = max(1.0, smoothing)
        self.margin_x = margin_x
        self.margin_y = margin_y
        self.cam_w = cam_w
        self.cam_h = cam_h

        # Coordinate state
        self.curr_x: float = self.screen_w / 2.0
        self.curr_y: float = self.screen_h / 2.0
        self.prev_x: float = self.curr_x
        self.prev_y: float = self.curr_y

        # Button state tracking
        self.is_left_down: bool = False
        self.is_right_down: bool = False

    def transform_coordinates(self, raw_x: float, raw_y: float) -> Tuple[int, int]:
        """
        Maps webcam coordinates (with inner margin rectangle) to full screen coordinates.
        Uses non-linear clamping to ensure user reaches screen edges comfortably.
        """
        # Usable active webcam tracking box
        active_w = max(1, self.cam_w - 2 * self.margin_x)
        active_h = max(1, self.cam_h - 2 * self.margin_y)

        # Normalize relative to active region
        norm_x = (raw_x - self.margin_x) / active_w
        norm_y = (raw_y - self.margin_y) / active_h

        # Clamp between 0.0 and 1.0
        norm_x = max(0.0, min(1.0, norm_x))
        norm_y = max(0.0, min(1.0, norm_y))

        # Map to display screen
        target_x = norm_x * self.screen_w
        target_y = norm_y * self.screen_h

        # Exponential Moving Average Smoothing
        self.curr_x = self.prev_x + (target_x - self.prev_x) / self.smoothing
        self.curr_y = self.prev_y + (target_y - self.prev_y) / self.smoothing

        self.prev_x = self.curr_x
        self.prev_y = self.curr_y

        # Clamp to safe screen pixels (prevent failsafe corner trigger)
        safe_x = int(max(2, min(self.screen_w - 2, self.curr_x)))
        safe_y = int(max(2, min(self.screen_h - 2, self.curr_y)))

        return safe_x, safe_y

    def move_to(self, target_x: int, target_y: int) -> None:
        """Move mouse cursor smoothly to target coordinates."""
        try:
            pyautogui.moveTo(target_x, target_y)
        except Exception:
            pass

    def click(self, button: str = "left") -> None:
        """Trigger instant mouse click."""
        try:
            pyautogui.click(button=button)
        except Exception:
            pass

    def double_click(self) -> None:
        """Trigger double click."""
        try:
            pyautogui.doubleClick()
        except Exception:
            pass

    def mouse_down(self, button: str = "left") -> None:
        """Depress mouse button for hold-and-drag interactions (e.g. Sliders, Window dragging)."""
        try:
            if button == "left" and not self.is_left_down:
                pyautogui.mouseDown(button="left")
                self.is_left_down = True
            elif button == "right" and not self.is_right_down:
                pyautogui.mouseDown(button="right")
                self.is_right_down = True
        except Exception:
            pass

    def mouse_up(self, button: str = "left") -> None:
        """Release mouse button from hold-and-drag state."""
        try:
            if button == "left" and self.is_left_down:
                pyautogui.mouseUp(button="left")
                self.is_left_down = False
            elif button == "right" and self.is_right_down:
                pyautogui.mouseUp(button="right")
                self.is_right_down = False
        except Exception:
            pass

    def scroll(self, steps: int) -> None:
        """Perform vertical mouse wheel scroll."""
        try:
            pyautogui.scroll(steps)
        except Exception:
            pass

    def release_all(self) -> None:
        """Safety cleanup: release any depressed mouse buttons."""
        if self.is_left_down:
            try:
                pyautogui.mouseUp(button="left")
            except Exception:
                pass
            self.is_left_down = False

        if self.is_right_down:
            try:
                pyautogui.mouseUp(button="right")
            except Exception:
                pass
            self.is_right_down = False
