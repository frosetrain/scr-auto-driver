import threading
import time

from pyscreenshot import grab
import pynput.keyboard
import pynput.mouse
import pytesseract

keyboard = pynput.keyboard.Controller()
mouse = pynput.mouse.Controller()


<<<<<<< HEAD
def change_throttle(percent):
    if percent > 0:
        keyboard.press('w')
        threading.Event().wait(0.033624 * percent)
        keyboard.release('w')
    elif percent < 0:
        keyboard.press('s')
        threading.Event().wait(0.03362 * abs(percent))
        keyboard.release('s')
=======
def increase_throttle(percent):
    keyboard.press('w')
    threading.Event().wait(0.033624 * percent)
    keyboard.release('w')


def decrease_throttle(percent):
    keyboard.press('s')
    threading.Event().wait(0.033624 * percent)
    keyboard.release('s')
>>>>>>> 126e4bc176ede68ec7e3d5d55ae45811f005ba5c


if __name__ == "__main__":
    while True:
        pic = grab(bbox=(1335, 992, 1378, 1011))
        pic.save("snip.jpg")
        print(pytesseract.image_to_string("snip.jpg", lang="osd"))
        time.sleep(2)
