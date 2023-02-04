#!/usr/bin/env python3

import logging
import threading
from time import sleep

import pynput.keyboard
import pynput.mouse
import pytesseract
from PIL import ImageGrab

keyboard = pynput.keyboard.Controller()
# mouse = pynput.mouse.Controller()

logging.getLogger("PIL.TiffImagePlugin").setLevel(logging.INFO)
logging.basicConfig(level="DEBUG")


TOP_SPEED = 100
THROTTLE_CHANGE_SPEED = 0.033624
SPEED_LIMIT_BBOX = (1561, 1352, 1594, 1373)
SIGNAL_LIGHT_BBOX = (2090, 1302, 2118, 1425)
SIGNAL_LIGHT_POINTS = ((14, 14), (14, 46), (14, 78), [14, 110])
AWS_BBOX = (2025, 1320, 2035, 1330)
AWS_POINT = (2030, 1325)


def get_speed_limit() -> int:
    pic = ImageGrab.grab(bbox=SPEED_LIMIT_BBOX)
    pic = pic.resize((99, 63))
    pic.save("speed_limit_snip.tif")
    speed_limit = pytesseract.image_to_string(
        "speed_limit_snip.tif", config="--psm 7 digits get.images"
    )
    speed_limit = speed_limit.strip()
    logging.debug(f"Tesseract returned {speed_limit}")
    try:
        speed_limit = int(speed_limit)
        if speed_limit <= 10:
            speed_limit = 75
        logging.debug(f"Succesfully read speed limit: {speed_limit}")
        last_successful_speed_limit = speed_limit
    except ValueError:
        try:
            speed_limit = last_successful_speed_limit
            logging.debug(f"Tesseract error, setting speed to {speed_limit}")
        except UnboundLocalError:
            return
    return speed_limit


def get_signal_limit() -> int:
    pic = ImageGrab.grab(bbox=SIGNAL_LIGHT_BBOX)
    pixels = pic.load()

    rgb_values = []
    for point in SIGNAL_LIGHT_POINTS:
        rgb_values.append(pixels[point[0], point[1]])

    aspect_colours = []
    for colour in rgb_values:
        r, g, b = colour
        if r < 10 and g > 240 and b < 10:  # Green
            aspect_colours.append("g")
        elif r > 240 and g > 180 and b < 10:  # Yellow
            aspect_colours.append("y")
        elif r > 240 and g < 10 and b < 10:  # Red
            aspect_colours.append("r")
        elif r > 240 and g > 240 and b > 240:  # White
            aspect_colours.append("w")
        elif r < 128 and g < 128 and b < 128:  # Black
            aspect_colours.append("b")

    if aspect_colours == ["b", "g", "b", "b"]:
        signal_limit = TOP_SPEED
    elif aspect_colours == ["y", "b", "y", "b"]:
        signal_limit = TOP_SPEED
    elif aspect_colours == ["b", "b", "y", "b"]:
        signal_limit = 45
    elif "r" in aspect_colours:
        signal_limit = 0
    else:
        signal_limit = 100

    return signal_limit


def handle_aws() -> None:
    pic = ImageGrab.grab(bbox=AWS_BBOX)
    pixels = pic.load()
    if pixels[AWS_POINT][0] > 240:
        keyboard.press("q")


def change_throttle(percent):
    if percent > 0:
        keyboard.press("w")
        threading.Event().wait(THROTTLE_CHANGE_SPEED * percent)
        keyboard.release("w")
    elif percent < 0:
        keyboard.press("s")
        threading.Event().wait(THROTTLE_CHANGE_SPEED * abs(percent))
        keyboard.release("s")


if __name__ == "__main__":
    current_target_speed = 0
    sleep(2)
    while True:
        got_speed_limit = get_speed_limit()
        got_signal_limit = get_signal_limit()
        if got_speed_limit is not None:
            new_target_speed = min(got_speed_limit, got_signal_limit)
        else:
            new_target_speed = got_signal_limit
        logging.debug(f"Target speed {new_target_speed}")
        if new_target_speed != current_target_speed:
            if new_target_speed > 0:
                throttle_change_amount = new_target_speed - current_target_speed
            elif new_target_speed == 0:
                throttle_change_amount = new_target_speed - current_target_speed - 5
            logging.info(f"Changing speed to {new_target_speed}")
            change_throttle(throttle_change_amount)
            current_target_speed = new_target_speed
        handle_aws()
        sleep(2)