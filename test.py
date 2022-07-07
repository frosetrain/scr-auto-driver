#!/usr/bin/env python3

import threading
from time import sleep

import pynput.keyboard
import pynput.mouse
import pytesseract
from PIL import ImageGrab

keyboard = pynput.keyboard.Controller()
# mouse = pynput.mouse.Controller()

THROTTLE_CHANGE_SPEED = 0.033624
SPEED_LIMIT_BBOX = (1561, 1353, 1594, 1370)
SIGNAL_LIGHT_BBOX = (2090, 1302, 2118, 1425)
SIGNAL_LIGHT_POINTS = ((14, 14), (14, 46), (14, 78), [14, 110])


def get_speed_limit() -> str:
    pic = ImageGrab.grab(bbox=SPEED_LIMIT_BBOX)
    pic.save("speed_limit_snip.tif")
    speed_limit = pytesseract.image_to_string(
        "speed_limit_snip.tif", config="--psm 7 digits"
    )
    speed_limit = speed_limit.strip()
    return speed_limit


def get_signal_limit() -> str:
    pic = ImageGrab.grab(bbox=SIGNAL_LIGHT_BBOX)
    pixels = pic.load()

    rgb_values = []
    for point in SIGNAL_LIGHT_POINTS:
        rgb_values.append(pixels[point[0], point[1]])

    aspect_colours = []
    for colour in rgb_values:
        r, g, b = colour
        if r < 10 and g > 240 and b < 10:  # Green
            aspect_colours.append("green")
        elif r > 240 and g > 180 and b < 10:  # Yellow
            aspect_colours.append("yellow")
        elif r > 240 and g < 10 and b < 10:  # Red
            aspect_colours.append("red")
        elif r > 240 and g > 240 and b > 240:  # White
            aspect_colours.append("white")
        elif r < 128 and g < 128 and b < 128:  # Grey
            aspect_colours.append("grey")

    return aspect_colours


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
    while True:
        # print(get_speed_limit())
        print(get_signal_limit())
        sleep(2)
