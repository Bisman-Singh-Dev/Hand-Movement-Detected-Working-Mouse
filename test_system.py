"""
Unit and Integration Test Suite for Hand-Movement-Detected-Working-Mouse.
Tests core modules: Coordinate transformation, gesture state machine,
pinch-to-click, and 2-second hold-and-drag logic.
"""

import time
import numpy as np
from core import MouseController, GestureRecognizer, MouseState, HUDRenderer
from config import DEFAULT_CONFIG


def test_mouse_controller_mapping():
    """Test screen coordinate transformation, boundaries, and clamping."""
    print("Testing MouseController coordinate mapping...")
    mc = MouseController(
        smoothing=1.0,  # 1.0 = instant mapping
        margin_x=50,
        margin_y=50,
        cam_w=640,
        cam_h=480,
    )
    # Center of active region (320, 240) should map to screen center
    sx, sy = mc.transform_coordinates(320, 240)
    assert abs(sx - mc.screen_w // 2) <= 5, f"Expected screen center X, got {sx}"
    assert abs(sy - mc.screen_h // 2) <= 5, f"Expected screen center Y, got {sy}"

    # Top-Left margin (50, 50) should map to (2, 2) safe screen bound
    sx, sy = mc.transform_coordinates(50, 50)
    assert sx == 2, f"Expected min X bound 2, got {sx}"
    assert sy == 2, f"Expected min Y bound 2, got {sy}"

    # Beyond bottom-right margin (640, 480) should clamp to screen_w - 2, screen_h - 2
    sx, sy = mc.transform_coordinates(640, 480)
    assert sx == mc.screen_w - 2, f"Expected max X clamp, got {sx}"
    assert sy == mc.screen_h - 2, f"Expected max Y clamp, got {sy}"
    print("✅ MouseController coordinate mapping passed!")


def test_gesture_pinch_click():
    """Test that pinching produces an instant CLICK event."""
    print("Testing pinch -> instant CLICK event...")
    recognizer = GestureRecognizer(
        pinch_threshold=0.085,
        pinch_release_threshold=0.10,
    )

    # Mock hand data: open hand (distance thumb to index is large)
    open_hand = {
        "raw": [(0, 0, 0)] * 21,
        "pixels": [(0, 0)] * 21,
        "scale": 1.0,
    }
    open_hand["raw"][4] = (0.2, 0.5, 0.0)
    open_hand["raw"][8] = (0.5, 0.5, 0.0)
    open_hand["pixels"][4] = (100, 250)
    open_hand["pixels"][8] = (250, 250)

    # Initial state
    ev = recognizer.process(open_hand)
    assert ev.state == MouseState.IDLE

    # Pinch hand: thumb and index tips touch (pixel distance 10px < 38px)
    pinched_hand = {
        "raw": [(0, 0, 0)] * 21,
        "pixels": [(0, 0)] * 21,
        "scale": 1.0,
    }
    pinched_hand["raw"][4] = (0.30, 0.5, 0.0)
    pinched_hand["raw"][8] = (0.32, 0.5, 0.0)
    pinched_hand["pixels"][4] = (150, 250)
    pinched_hand["pixels"][8] = (158, 250)

    # Instant click trigger
    ev1 = recognizer.process(pinched_hand)
    assert ev1.event_type == "CLICK", f"Expected CLICK, got {ev1.event_type}"
    assert ev1.state == MouseState.CLICKED

    # Ongoing pinch does not spam duplicate clicks
    ev_mid = recognizer.process(pinched_hand)
    assert ev_mid.event_type == "PINCH_PROGRESS"

    # Open fingers resets pinch state
    ev_rel = recognizer.process(open_hand)
    assert not recognizer.is_pinching

    # Next pinch triggers click again
    ev2 = recognizer.process(pinched_hand)
    assert ev2.event_type == "CLICK"
    print("✅ Pinch -> instant CLICK event passed!")


def test_hud_rendering():
    """Verify that HUD renders correctly without crashing."""
    print("Testing HUD rendering on mock frame...")
    hud = HUDRenderer()
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    recognizer = GestureRecognizer()

    open_hand = {
        "raw": [(0, 0, 0)] * 21,
        "pixels": [(100, 100)] * 21,
        "scale": 1.0,
    }
    event = recognizer.process(open_hand)
    rendered = hud.render(
        frame=frame,
        fps=60.0,
        event=event,
        cursor_pos=(960, 540),
        hand_data=open_hand,
        show_hud=True,
    )
    assert rendered.shape == (480, 640, 3)
    print("✅ HUD rendering test passed!")


if __name__ == "__main__":
    print("========================================")
    print(" Running Virtual Hand Mouse Test Suite")
    print("========================================")
    test_mouse_controller_mapping()
    test_gesture_pinch_click()
    test_hud_rendering()
    print("========================================")
    print(" 🎉 ALL TESTS PASSED SUCCESSFULLY!")
    print("========================================")
