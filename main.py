"""
Main Application Entrypoint for Hand-Movement-Detected-Working-Mouse.
Integrates computer vision tracking, real-time gesture recognition,
smooth virtual mouse control, and HUD feedback.
"""

import argparse
import sys
import time
import cv2
import pyautogui

from config import DEFAULT_CONFIG, AppConfig
from core import HandTracker, MouseController, GestureRecognizer, HUDRenderer, MouseState


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Hand-Movement-Detected-Working-Mouse: AI Virtual Mouse Control"
    )
    parser.add_argument(
        "--camera",
        type=int,
        default=DEFAULT_CONFIG.CAMERA_INDEX,
        help="Webcam device index (default: 0)",
    )
    parser.add_argument(
        "--smoothing",
        type=float,
        default=DEFAULT_CONFIG.SMOOTHING_FACTOR,
        help="Cursor smoothing factor (default: 5.0)",
    )
    parser.add_argument(
        "--hold-seconds",
        type=float,
        default=DEFAULT_CONFIG.HOLD_DELAY_SECONDS,
        help="Pinch hold threshold in seconds before drag activates (default: 2.0)",
    )
    parser.add_argument(
        "--no-hud",
        action="store_true",
        help="Disable on-screen heads up display",
    )
    parser.add_argument(
        "--no-mirror",
        action="store_true",
        help="Disable camera horizontal mirror flip",
    )
    return parser.parse_args()


def run_hand_mouse(config: AppConfig = DEFAULT_CONFIG, args: argparse.Namespace = None):
    # Override config with any CLI flags
    cam_index = args.camera if args else config.CAMERA_INDEX
    smoothing = args.smoothing if args else config.SMOOTHING_FACTOR
    hold_delay = args.hold_seconds if args else config.HOLD_DELAY_SECONDS
    show_hud = not args.no_hud if args else config.SHOW_HUD
    mirror = not args.no_mirror if args else config.FLIP_HORIZONTAL

    print("==================================================================")
    print(" 🖐️  HAND MOVEMENT DETECTED - VIRTUAL WORKING MOUSE PRO")
    print("==================================================================")
    print(f" Camera Index        : {cam_index}")
    print(f" Smoothing Factor    : {smoothing}")
    print(f" Pinch Hold Threshold: {hold_delay:.1f} seconds (Slider / Drag mode)")
    print("------------------------------------------------------------------")
    print(" Controls:")
    print("   • Move Index Finger       : Moves mouse cursor")
    print("   • Pinch Index + Thumb     : Instant Left Click")
    print("   • Middle + Thumb Pinch    : Right Click")
    print("   • Index + Middle Up       : Vertical Page Scroll")
    print("   • [Q] or [ESC]            : Quit Application")
    print("   • [P]                     : Pause / Resume Tracking")
    print("   • [H]                     : Toggle HUD Overlay")
    print("==================================================================")

    # Initialize video capture
    cap = cv2.VideoCapture(cam_index)
    if not cap.isOpened():
        print(f"⚠️ Warning: Unable to open webcam at index {cam_index}. Trying index 1...")
        cap = cv2.VideoCapture(1)
        if not cap.isOpened():
            print("❌ Error: No webcam detected. Please connect a camera and try again.")
            return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.CAMERA_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.CAMERA_HEIGHT)

    # Initialize subsystems
    tracker = HandTracker(
        mode=False,
        max_hands=1,
        detection_con=0.7,
        track_con=0.7,
    )
    mouse = MouseController(
        smoothing=smoothing,
        margin_x=config.FRAME_MARGIN_X,
        margin_y=config.FRAME_MARGIN_Y,
        cam_w=config.CAMERA_WIDTH,
        cam_h=config.CAMERA_HEIGHT,
    )
    recognizer = GestureRecognizer(
        pinch_threshold=config.PINCH_THRESHOLD,
        pinch_release_threshold=config.PINCH_RELEASE_THRESHOLD,
        hold_delay_seconds=hold_delay,
        min_click_duration=config.MIN_CLICK_DURATION,
        max_click_duration=config.MAX_CLICK_DURATION,
        right_click_enabled=config.RIGHT_CLICK_ENABLED,
        scroll_enabled=config.SCROLL_ENABLED,
    )
    hud = HUDRenderer(
        margin_x=config.FRAME_MARGIN_X,
        margin_y=config.FRAME_MARGIN_Y,
        hold_delay_seconds=hold_delay,
    )

    is_paused = False
    prev_time = time.time()
    fps = 30.0

    screen_w, screen_h = pyautogui.size()
    cursor_pos = (screen_w // 2, screen_h // 2)

    window_name = config.WINDOW_TITLE
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, config.CAMERA_WIDTH, config.CAMERA_HEIGHT)

    try:
        while True:
            success, frame = cap.read()
            if not success or frame is None:
                time.sleep(0.01)
                continue

            # Calculate FPS
            curr_time = time.time()
            dt = curr_time - prev_time
            if dt > 0:
                fps = 0.9 * fps + 0.1 * (1.0 / dt)
            prev_time = curr_time

            # Mirror webcam feed for intuitive movement
            if mirror:
                frame = cv2.flip(frame, 1)

            # Hand tracking
            frame, hand_data = tracker.find_hands(frame, draw=False)

            # Process gestures
            event = recognizer.process(hand_data)

            if hand_data and not is_paused:
                # Track cursor anchor: Index finger tip (Landmark 8)
                index_pixel = hand_data["pixels"][8]
                screen_x, screen_y = mouse.transform_coordinates(
                    index_pixel[0], index_pixel[1]
                )
                cursor_pos = (screen_x, screen_y)

                # Move cursor
                mouse.move_to(screen_x, screen_y)

                # Execute recognized gestures
                if event.event_type == "CLICK":
                    mouse.click("left")
                    print(f"🖱️ [CLICK] Left Click at ({screen_x}, {screen_y})")

                elif event.event_type == "HOLD_START":
                    mouse.mouse_down("left")
                    print(f"🔒 [HOLD START] 2s Pinch Triggered - Slider / Drag Active at ({screen_x}, {screen_y})")

                elif event.event_type == "HOLD_RELEASE":
                    mouse.mouse_up("left")
                    print(f"🔓 [HOLD RELEASE] Mouse Released at ({screen_x}, {screen_y})")

                elif event.event_type == "RIGHT_CLICK":
                    mouse.click("right")
                    print(f"🖱️ [RIGHT CLICK] at ({screen_x}, {screen_y})")

                elif event.event_type == "SCROLL":
                    mouse.scroll(event.scroll_delta)

            # Render visual HUD
            display_frame = hud.render(
                frame=frame,
                fps=fps,
                event=event,
                cursor_pos=cursor_pos,
                hand_data=hand_data,
                show_hud=show_hud,
                is_paused=is_paused,
            )

            cv2.imshow(window_name, display_frame)

            # Keyboard handler
            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), ord("Q"), 27):  # 'q' or ESC
                print("🛑 Exiting application...")
                break
            elif key in (ord("p"), ord("P")):
                is_paused = not is_paused
                status = "PAUSED" if is_paused else "RESUMED"
                print(f"⏸️ Tracking {status}")
                if is_paused:
                    mouse.release_all()
            elif key in (ord("h"), ord("H")):
                show_hud = not show_hud
                print(f"📺 HUD {'Enabled' if show_hud else 'Disabled'}")
            elif key in (ord("r"), ord("R")):
                mouse.release_all()
                print("🔄 Mouse states reset")

    except KeyboardInterrupt:
        print("\nInterrupted by user.")
    finally:
        # Safe cleanup
        mouse.release_all()
        tracker.close()
        cap.release()
        cv2.destroyAllWindows()
        print("✅ Clean shutdown completed.")


if __name__ == "__main__":
    cli_args = parse_arguments()
    run_hand_mouse(DEFAULT_CONFIG, cli_args)
