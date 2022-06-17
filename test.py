import threading
import time

import pynput.keyboard
import pynput.mouse
import pytesseract
from PIL import Image
from pyscreenshot import grab

keyboard = pynput.keyboard.Controller()
mouse = pynput.mouse.Controller()

THROTTLE_CHANGE_SPEED = 0.033624
SPEED_LIMIT_BBOX = (1862, 994, 1893, 1009)


def change_throttle(percent):
    if percent > 0:
        keyboard.press("w")
        threading.Event().wait(THROTTLE_CHANGE_SPEED * percent)
        keyboard.release("w")
    elif percent < 0:
        keyboard.press("s")
        threading.Event().wait(THROTTLE_CHANGE_SPEED * abs(percent))
        keyboard.release("s")


def get_speed_limit(bbox):
    pic = grab(bbox=SPEED_LIMIT_BBOX)
    pic.save("snip.tif")
    pic = Image.open("snip.tif")
    pic = pic.resize((62, 30))
    speed_limit = pytesseract.image_to_string("snip.tif", config="--psm 7 digits")
    speed_limit = speed_limit.strip(" \n")
    return speed_limit


if __name__ == "__main__":
    while True:
        print(get_speed_limit(SPEED_LIMIT_BBOX))
        time.sleep(2)
