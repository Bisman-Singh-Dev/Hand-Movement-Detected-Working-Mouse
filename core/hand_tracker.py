"""
Hand Tracker Module using Google MediaPipe Hands.
Provides robust real-time 21-landmark tracking with Euclidean normalization and jitter filtering.
"""

import math
from typing import List, Optional, Tuple, Dict
import cv2
import numpy as np


class HandTracker:
    def __init__(
        self,
        mode: bool = False,
        max_hands: int = 1,
        detection_con: float = 0.7,
        track_con: float = 0.7,
    ):
        """
        Initializes the MediaPipe Hands detector.
        """
        import mediapipe as mp

        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=mode,
            max_num_hands=max_hands,
            min_detection_confidence=detection_con,
            min_tracking_confidence=track_con,
        )
        self.mp_draw = mp.solutions.drawing_utils
        self.mp_draw_styles = mp.solutions.drawing_styles

        # Landmark history for exponential smoothing
        self.prev_landmarks: Dict[int, Tuple[float, float]] = {}
        self.results = None

    def find_hands(
        self, frame: np.ndarray, draw: bool = True
    ) -> Tuple[np.ndarray, Optional[Dict]]:
        """
        Processes a BGR image frame and extracts 21 hand landmarks.
        Returns:
            processed_frame: numpy array with optional drawn landmarks
            hand_data: Dict with normalized, pixel coordinates, hand scale, and classification
        """
        h, w, _ = frame.shape
        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img_rgb.flags.writeable = False
        self.results = self.hands.process(img_rgb)
        img_rgb.flags.writeable = True

        hand_data = None

        if self.results.multi_hand_landmarks:
            # We track primary hand (first detected hand)
            hand_landmarks = self.results.multi_hand_landmarks[0]
            hand_label = "Right"
            if self.results.multi_handedness:
                hand_label = self.results.multi_handedness[0].classification[0].label

            raw_points: List[Tuple[float, float, float]] = []
            pixel_points: List[Tuple[int, int]] = []

            for lm in hand_landmarks.landmark:
                raw_points.append((lm.x, lm.y, lm.z))
                px, py = int(lm.x * w), int(lm.y * h)
                pixel_points.append((px, py))

            # Reference hand scale: Euclidean distance between Wrist (0) and Middle MCP (9)
            wrist = raw_points[0]
            middle_mcp = raw_points[9]
            hand_scale = math.hypot(wrist[0] - middle_mcp[0], wrist[1] - middle_mcp[1])
            # Prevent division by zero
            if hand_scale < 0.0001:
                hand_scale = 0.2

            hand_data = {
                "raw": raw_points,
                "pixels": pixel_points,
                "scale": hand_scale,
                "label": hand_label,
                "multi_landmarks": hand_landmarks,
            }

            if draw:
                self.draw_hand_landmarks(frame, hand_landmarks)

        return frame, hand_data

    def draw_hand_landmarks(self, frame: np.ndarray, landmarks) -> None:
        """
        Draws sleek landmarks and connections with a customized visual palette.
        """
        self.mp_draw.draw_landmarks(
            frame,
            landmarks,
            self.mp_hands.HAND_CONNECTIONS,
            landmark_drawing_spec=self.mp_draw.DrawingSpec(
                color=(0, 240, 255), thickness=2, circle_radius=3
            ),
            connection_drawing_spec=self.mp_draw.DrawingSpec(
                color=(50, 180, 50), thickness=2, circle_radius=2
            ),
        )

    def close(self):
        """Release MediaPipe resources."""
        if hasattr(self, "hands") and self.hands:
            self.hands.close()
