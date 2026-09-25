"""
Gesture Recognizer Module.
Implements state machine for:
1. Hand Tracking Cursor Movement
2. Pinch Detection (Index Tip + Thumb Tip)
3. Instant Click on Release (< 2.0s)
4. 2-Second Hold-and-Drag (e.g. Sliders, Window Dragging) when pinch held >= 2.0s
5. Secondary gestures: Right-click pinch (Middle + Thumb) and Dual-Finger Scroll
"""

import math
import time
from enum import Enum, auto
from typing import Dict, Optional, Tuple


class MouseState(Enum):
    IDLE = auto()
    PINCHING = auto()
    HOLDING = auto()
    CLICKED = auto()
    RIGHT_CLICK = auto()
    SCROLLING = auto()


class GestureEvent:
    def __init__(
        self,
        event_type: str,
        state: MouseState,
        progress: float = 0.0,
        elapsed_sec: float = 0.0,
        pinch_center: Optional[Tuple[int, int]] = None,
        scroll_delta: int = 0,
    ):
        self.event_type = event_type
        self.state = state
        self.progress = max(0.0, min(1.0, progress))
        self.elapsed_sec = elapsed_sec
        self.pinch_center = pinch_center
        self.scroll_delta = scroll_delta


class GestureRecognizer:
    def __init__(
        self,
        pinch_threshold: float = 0.065,
        pinch_release_threshold: float = 0.085,
        hold_delay_seconds: float = 2.0,
        min_click_duration: float = 0.05,
        max_click_duration: float = 1.95,
        right_click_enabled: bool = True,
        scroll_enabled: bool = True,
    ):
        self.pinch_threshold = pinch_threshold
        self.pinch_release_threshold = pinch_release_threshold
        self.hold_delay_seconds = hold_delay_seconds
        self.min_click_duration = min_click_duration
        self.max_click_duration = max_click_duration
        self.right_click_enabled = right_click_enabled
        self.scroll_enabled = scroll_enabled

        # State tracking
        self.is_pinching: bool = False
        self.is_holding: bool = False
        self.pinch_start_time: Optional[float] = None
        self.current_state: MouseState = MouseState.IDLE

        # Right click state
        self.is_right_pinching: bool = False
        self.right_pinch_start_time: Optional[float] = None

        # Scroll tracking
        self.prev_scroll_y: Optional[int] = None

        # Click visual feedback timer
        self.last_click_time: float = 0.0

    def compute_distance(
        self, pt1: Tuple[float, float, float], pt2: Tuple[float, float, float]
    ) -> float:
        """Euclidean distance in 3D landmark space."""
        return math.sqrt(
            (pt1[0] - pt2[0]) ** 2 + (pt1[1] - pt2[1]) ** 2 + (pt1[2] - pt2[2]) ** 2
        )

    def process(self, hand_data: Optional[Dict]) -> GestureEvent:
        """
        Processes hand landmarks and yields real-time gesture events and hold progress.
        """
        current_time = time.time()

        # If no hand detected, release any active holds safely
        if not hand_data:
            if self.is_holding:
                self.is_holding = False
                self.is_pinching = False
                self.pinch_start_time = None
                self.current_state = MouseState.IDLE
                return GestureEvent("HOLD_RELEASE", MouseState.IDLE)
            self.is_pinching = False
            self.pinch_start_time = None
            self.current_state = MouseState.IDLE
            return GestureEvent("NONE", MouseState.IDLE)

        raw_points = hand_data["raw"]
        pixel_points = hand_data["pixels"]
        hand_scale = hand_data["scale"]

        # Landmark indexes:
        # 4: Thumb Tip, 8: Index Tip, 12: Middle Tip, 16: Ring Tip, 20: Pinky Tip
        thumb_tip = raw_points[4]
        index_tip = raw_points[8]
        middle_tip = raw_points[12]
        ring_tip = raw_points[16]
        pinky_tip = raw_points[20]

        # Normalized distances (invariant to camera distance)
        dist_thumb_index = self.compute_distance(thumb_tip, index_tip) / hand_scale
        dist_thumb_middle = self.compute_distance(thumb_tip, middle_tip) / hand_scale

        # Pinch center in pixel coordinates for HUD graphics
        p1 = pixel_points[4]
        p2 = pixel_points[8]
        pinch_center = ((p1[0] + p2[0]) // 2, (p1[1] + p2[1]) // 2)

        # -------------------------------------------------------------
        # 1. PRIMARY PINCH DETECTION (INDEX + THUMB) -> INSTANT CLICK
        # -------------------------------------------------------------
        # Pixel distance between index fingertip (8) and thumb tip (4)
        pixel_dist = math.hypot(p1[0] - p2[0], p1[1] - p2[1])

        # A pinch occurs if normalized distance is small OR pixel distance is close (< 38px)
        is_pinch_active = (dist_thumb_index < self.pinch_threshold) or (pixel_dist < 38)

        if is_pinch_active:
            if not self.is_pinching:
                # Instant click trigger as soon as pinch touches!
                self.is_pinching = True
                self.pinch_start_time = current_time
                self.last_click_time = current_time
                self.current_state = MouseState.CLICKED
                return GestureEvent(
                    "CLICK",
                    MouseState.CLICKED,
                    progress=1.0,
                    elapsed_sec=0.0,
                    pinch_center=pinch_center,
                )
            else:
                self.current_state = MouseState.PINCHING
                return GestureEvent(
                    "PINCH_PROGRESS",
                    MouseState.PINCHING,
                    progress=1.0,
                    elapsed_sec=current_time - (self.pinch_start_time or current_time),
                    pinch_center=pinch_center,
                )
        else:
            if self.is_pinching:
                self.is_pinching = False
                self.pinch_start_time = None

        # -------------------------------------------------------------
        # 2. SECONDARY GESTURE: RIGHT CLICK PINCH (MIDDLE + THUMB)
        # -------------------------------------------------------------
        if self.right_click_enabled and not self.is_pinching and not self.is_holding:
            is_right_active = (
                dist_thumb_middle < self.pinch_threshold
                if not self.is_right_pinching
                else dist_thumb_middle < self.pinch_release_threshold
            )
            if is_right_active:
                if not self.is_right_pinching:
                    self.is_right_pinching = True
                    self.right_pinch_start_time = current_time
            else:
                if self.is_right_pinching:
                    elapsed = (
                        (current_time - self.right_pinch_start_time)
                        if self.right_pinch_start_time
                        else 0.0
                    )
                    self.is_right_pinching = False
                    self.right_pinch_start_time = None
                    if self.min_click_duration <= elapsed <= 1.2:
                        p_mid = pixel_points[12]
                        mid_center = ((p1[0] + p_mid[0]) // 2, (p1[1] + p_mid[1]) // 2)
                        self.current_state = MouseState.RIGHT_CLICK
                        return GestureEvent(
                            "RIGHT_CLICK",
                            MouseState.RIGHT_CLICK,
                            progress=0.0,
                            elapsed_sec=elapsed,
                            pinch_center=mid_center,
                        )

        # -------------------------------------------------------------
        # 3. SECONDARY GESTURE: TWO-FINGER VERTICAL SCROLL
        # -------------------------------------------------------------
        if self.scroll_enabled and not self.is_pinching and not self.is_holding:
            # Check if index and middle finger tips are up and other fingers down
            is_index_extended = raw_points[8][1] < raw_points[6][1]
            is_middle_extended = raw_points[12][1] < raw_points[10][1]
            is_ring_folded = raw_points[16][1] > raw_points[14][1]
            is_pinky_folded = raw_points[20][1] > raw_points[18][1]

            dist_index_middle = (
                self.compute_distance(index_tip, middle_tip) / hand_scale
            )

            if (
                is_index_extended
                and is_middle_extended
                and is_ring_folded
                and is_pinky_folded
                and dist_index_middle < 0.12
            ):
                avg_y = (pixel_points[8][1] + pixel_points[12][1]) // 2
                scroll_delta = 0
                if self.prev_scroll_y is not None:
                    diff_y = self.prev_scroll_y - avg_y
                    if abs(diff_y) > 4:
                        scroll_delta = int(diff_y * 3)
                self.prev_scroll_y = avg_y
                if scroll_delta != 0:
                    self.current_state = MouseState.SCROLLING
                    return GestureEvent(
                        "SCROLL",
                        MouseState.SCROLLING,
                        scroll_delta=scroll_delta,
                    )
            else:
                self.prev_scroll_y = None

        # Flash click badge if within 0.2s of click
        if current_time - self.last_click_time < 0.25:
            self.current_state = MouseState.CLICKED
        else:
            self.current_state = MouseState.IDLE

        return GestureEvent("TRACKING", self.current_state)
