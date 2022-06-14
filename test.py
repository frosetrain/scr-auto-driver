import threading
import time

from pynput.keyboard import Key, Controller

keyboard = Controller()


def increase_throttle(percent):
    keyboard.press('w')
    threading.Event().wait(0.033624 * percent)
    keyboard.release('w')


def decrease_throttle(percent):
    keyboard.press('s')
    threading.Event().wait(0.03362 * percent)
    keyboard.release('s')


if __name__ == "__main__":
    time.sleep(2)
    print("lets go")
    increase_throttle(10)
    time.sleep(10)
    decrease_throttle(10)
    print("done")
