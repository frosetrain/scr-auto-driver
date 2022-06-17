import threading
import time

from pyscreenshot import grab
import pynput.keyboard
import pynput.mouse
import pytesseract

keyboard = pynput.keyboard.Controller()
mouse = pynput.mouse.Controller()


def change_throttle(percent):
    if percent > 0:
        keyboard.press('w')
        threading.Event().wait(0.033624 * percent)
        keyboard.release('w')
    elif percent < 0:
        keyboard.press('s')
        threading.Event().wait(0.03362 * abs(percent))
        keyboard.release('s')


if __name__ == "__main__":
    while True:
        pic = grab(bbox=(1335, 992, 1378, 1011))
        pic.save("snip.jpg")
        print(pytesseract.image_to_string("snip.jpg", lang="osd"))
        time.sleep(2)
