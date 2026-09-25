"""
HUD Renderer Module.
Draws a futuristic, responsive heads-up display overlay on OpenCV frames,
including circular pinch-hold progress rings, active bounding boxes,
state badges, and interactive feedback ripples.
"""

import math
import time
from typing import Dict, Optional, Tuple
import cv2
import numpy as np

from .gesture_recognizer import GestureEvent, MouseState


class HUDRenderer:
    def __init__(
        self,
        margin_x: int = 80,
        margin_y: int = 60,
        hold_delay_seconds: float = 2.0,
    ):
        self.margin_x = margin_x
        self.margin_y = margin_y
        self.hold_delay_seconds = hold_delay_seconds

        # Ripple animation states for click feedback
        self.ripples = []

    def add_click_ripple(self, center: Tuple[int, int], color: Tuple[int, int, int] = (255, 255, 255)):
        """Trigger an expanding ripple animation on click."""
        self.ripples.append({
            "center": center,
            "radius": 15,
            "max_radius": 50,
            "alpha": 1.0,
            "color": color,
            "created_at": time.time()
        })

    def update_and_draw_ripples(self, frame: np.ndarray):
        """Update and render active ripple circles."""
        current_time = time.time()
        alive_ripples = []
        h, w, _ = frame.shape

        for r in self.ripples:
            age = current_time - r["created_at"]
            if age < 0.35:
                progress = age / 0.35
                radius = int(r["radius"] + progress * (r["max_radius"] - r["radius"]))
                alpha = 1.0 - progress
                
                # Draw translucent ring
                overlay = frame.copy()
                cv2.circle(overlay, r["center"], radius, r["color"], 3, cv2.LINE_AA)
                cv2.addWeighted(overlay, alpha, frame, 1.0 - alpha, 0, frame)
                alive_ripples.append(r)

        self.ripples = alive_ripples

    def draw_active_boundary(self, frame: np.ndarray, color=(255, 200, 0)):
        """Draws the screen-mapping boundary box with futuristic corner brackets."""
        h, w, _ = frame.shape
        x1, y1 = self.margin_x, self.margin_y
        x2, y2 = w - self.margin_x, h - self.margin_y

        # Draw semi-transparent boundary box
        overlay = frame.copy()
        cv2.rectangle(overlay, (x1, y1), (x2, y2), color, 1, cv2.LINE_AA)
        cv2.addWeighted(overlay, 0.4, frame, 0.6, 0, frame)

        # Draw corner brackets
        corner_len = 22
        thickness = 3
        # Top-Left
        cv2.line(frame, (x1, y1), (x1 + corner_len, y1), color, thickness)
        cv2.line(frame, (x1, y1), (x1, y1 + corner_len), color, thickness)
        # Top-Right
        cv2.line(frame, (x2, y1), (x2 - corner_len, y1), color, thickness)
        cv2.line(frame, (x2, y1), (x2, y1 + corner_len), color, thickness)
        # Bottom-Left
        cv2.line(frame, (x1, y2), (x1 + corner_len, y2), color, thickness)
        cv2.line(frame, (x1, y2), (x1, y2 - corner_len), color, thickness)
        # Bottom-Right
        cv2.line(frame, (x2, y2), (x2 - corner_len, y2), color, thickness)
        cv2.line(frame, (x2, y2), (x2, y2 - corner_len), color, thickness)

    def draw_pinch_progress_ring(
        self,
        frame: np.ndarray,
        center: Tuple[int, int],
        progress: float,
        is_holding: bool,
    ):
        """
        Draws visual feedback ring at the pinch point.
        """
        cx, cy = center
        radius = 28
        # Instant click feedback circle
        cv2.circle(frame, (cx, cy), radius, (0, 255, 255), 3, cv2.LINE_AA)
        cv2.circle(frame, (cx, cy), 6, (255, 255, 255), -1, cv2.LINE_AA)
        cv2.putText(
            frame,
            "PINCH CLICK",
            (cx - 45, cy - radius - 8),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (0, 255, 255),
            1,
            cv2.LINE_AA,
        )

    def draw_top_bar(
        self,
        frame: np.ndarray,
        fps: float,
        event: GestureEvent,
        cursor_pos: Tuple[int, int],
        is_paused: bool = False,
    ):
        """Draws top status header with glassmorphism card and status badges."""
        h, w, _ = frame.shape

        # Header background banner
        header_h = 46
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, header_h), (18, 18, 22), -1)
        cv2.addWeighted(overlay, 0.85, frame, 0.15, 0, frame)

        # Bottom accent divider line
        cv2.line(frame, (0, header_h), (w, header_h), (60, 60, 75), 1)

        # Title & App Branding
        cv2.circle(frame, (18, 23), 6, (0, 230, 255), -1, cv2.LINE_AA)
        cv2.putText(
            frame,
            "HAND MOUSE PRO",
            (32, 28),
            cv2.FONT_HERSHEY_DUPLEX,
            0.6,
            (255, 255, 255),
            1,
            cv2.LINE_AA,
        )

        # FPS Readout
        fps_text = f"{int(fps)} FPS"
        cv2.putText(
            frame,
            fps_text,
            (210, 28),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (160, 220, 160),
            1,
            cv2.LINE_AA,
        )

        # State Badge
        state_badge = "TRACKING"
        badge_color = (80, 200, 100)  # Green

        if is_paused:
            state_badge = "PAUSED [P]"
            badge_color = (120, 120, 120)
        elif event.state == MouseState.HOLDING:
            state_badge = f"HOLDING / DRAG [{event.elapsed_sec:.1f}s]"
            badge_color = (0, 150, 255)  # Orange
        elif event.state == MouseState.PINCHING:
            state_badge = f"PINCHING ({int(event.progress * 100)}%)"
            badge_color = (255, 200, 0)  # Cyan
        elif event.state == MouseState.CLICKED:
            state_badge = "CLICK!"
            badge_color = (255, 255, 255)  # White
        elif event.state == MouseState.RIGHT_CLICK:
            state_badge = "RIGHT CLICK"
            badge_color = (230, 80, 180)  # Purple
        elif event.state == MouseState.SCROLLING:
            state_badge = "SCROLLING"
            badge_color = (200, 120, 255)

        # Render pill badge
        bx1 = w - 240
        bx2 = w - 15
        by1 = 8
        by2 = 38
        cv2.rectangle(frame, (bx1, by1), (bx2, by2), (35, 35, 45), -1)
        cv2.rectangle(frame, (bx1, by1), (bx2, by2), badge_color, 1, cv2.LINE_AA)
        cv2.circle(frame, (bx1 + 14, 23), 5, badge_color, -1, cv2.LINE_AA)
        cv2.putText(
            frame,
            state_badge,
            (bx1 + 28, 27),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            badge_color,
            1,
            cv2.LINE_AA,
        )

    def draw_footer_legend(self, frame: np.ndarray, cursor_pos: Tuple[int, int]):
        """Renders bottom toolbar with keyboard shortcuts and cursor coordinates."""
        h, w, _ = frame.shape
        footer_h = 32
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, h - footer_h), (w, h), (15, 15, 20), -1)
        cv2.addWeighted(overlay, 0.85, frame, 0.15, 0, frame)

        # Coordinate indicator
        coord_text = f"Cursor: ({cursor_pos[0]}, {cursor_pos[1]})"
        cv2.putText(
            frame,
            coord_text,
            (15, h - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.42,
            (200, 200, 200),
            1,
            cv2.LINE_AA,
        )

        # Hotkey instructions
        legend_text = "[Q] Quit  |  [P] Pause  |  [H] HUD  |  Pinch = Click"
        cv2.putText(
            frame,
            legend_text,
            (w - 380, h - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.40,
            (160, 160, 175),
            1,
            cv2.LINE_AA,
        )

    def render(
        self,
        frame: np.ndarray,
        fps: float,
        event: GestureEvent,
        cursor_pos: Tuple[int, int],
        hand_data: Optional[Dict],
        show_hud: bool = True,
        is_paused: bool = False,
    ) -> np.ndarray:
        """Full composite render of all HUD components onto frame."""
        if not show_hud:
            return frame

        # Active boundary box
        self.draw_active_boundary(frame)

        # Click ripple feedback
        if event.state == MouseState.CLICKED and event.pinch_center:
            self.add_click_ripple(event.pinch_center, (255, 255, 255))
        elif event.state == MouseState.RIGHT_CLICK and event.pinch_center:
            self.add_click_ripple(event.pinch_center, (230, 80, 180))

        self.update_and_draw_ripples(frame)

        # Pinch circular progress indicator
        if event.pinch_center and (
            event.state in (MouseState.PINCHING, MouseState.HOLDING)
        ):
            self.draw_pinch_progress_ring(
                frame,
                event.pinch_center,
                event.progress,
                event.state == MouseState.HOLDING,
            )

        # Top Header & Footer
        self.draw_top_bar(frame, fps, event, cursor_pos, is_paused)
        self.draw_footer_legend(frame, cursor_pos)

        return frame
