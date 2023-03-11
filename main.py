import logging
from os import system
from threading import Event
from time import sleep

import pynput.keyboard
import pytesseract
from PIL import ImageGrab

window = (0, 100, 1920, 1180)
speed_limit_bbox = (window[0] + 865, window[1] + 940, window[0] + 925, window[1] + 980)
signal_bbox = (1685, window[1] + 893, 1686, window[1] + 1040)
signal_points = ((0, 0), (0, 49), (0, 98), (0, 146))
aws_bbox = (1430, 1060, 1431, 1061)
top_speed = 100
throttle_change_speed = 0.033624

keyboard = pynput.keyboard.Controller()

logging.getLogger("PIL.TiffImagePlugin").setLevel(logging.INFO)
logging.basicConfig(level="DEBUG")


def get_speed_limit() -> int:
    pic = ImageGrab.grab(bbox=speed_limit_bbox)
    pic = pic.resize((90, 60))
    pic.save("speed_limit.tif")
    speed_limit = pytesseract.image_to_string(
        "speed_limit.tif", config="--psm 7 digits get.images"
    )
    speed_limit = speed_limit.strip()
    try:
        speed_limit = int(speed_limit)
        logging.debug(f"Speed limit: {speed_limit}")
    except ValueError:
        logging.debug(f"Tesseract error: {speed_limit}")
    return speed_limit


def get_signal_limit() -> int:
    pic = ImageGrab.grab(bbox=signal_bbox)
    pic.save("signal.tif")
    pixels = pic.load()

    rgb_values = []
    for point in signal_points:
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
        signal_limit = top_speed
    elif aspect_colours == ["y", "b", "y", "b"]:
        signal_limit = top_speed
    elif aspect_colours == ["b", "b", "y", "b"]:
        signal_limit = 45
    elif "r" in aspect_colours:
        signal_limit = 0
    else:
        signal_limit = 100

    logging.debug(f"Signal limit: {signal_limit}")
    return signal_limit


def change_throttle(percent):
    if percent > 0:
        keyboard.press("w")
        Event().wait(throttle_change_speed * percent)
        keyboard.release("w")
    elif percent < 0:
        keyboard.press("s")
        Event().wait(throttle_change_speed * abs(percent))
        keyboard.release("s")


def handle_aws() -> None:
    pic = ImageGrab.grab(bbox=aws_bbox)
    pixels = pic.load()
    if pixels[0, 0][0] > 240:
        keyboard.press("q")
        logging.debug("AWS")


if __name__ == "__main__":
    current_target_speed = 0
    sleep(2)
    while True:
        system("clear")
        got_speed_limit = get_speed_limit()
        got_signal_limit = get_signal_limit()
        if isinstance(got_speed_limit, int):
            new_target_speed = min(got_speed_limit, got_signal_limit)
        else:
            new_target_speed = got_signal_limit
        logging.debug(f"Target speed: {new_target_speed}")
        if new_target_speed != current_target_speed:
            if new_target_speed > 0:
                throttle_change_amount = new_target_speed - current_target_speed
            elif new_target_speed == 0:
                throttle_change_amount = new_target_speed - current_target_speed - 5
            logging.info(f"Changing speed to {new_target_speed}")
            change_throttle(throttle_change_amount)
            current_target_speed = new_target_speed
        handle_aws()
        sleep(0.5)
