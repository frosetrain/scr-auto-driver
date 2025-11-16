from pynput.keyboard import Controller
from time import sleep

keyboard = Controller()
top_speed = 100
throttle_change_speed = 0.04035789


def change_throttle(start, end) -> None:
    if end == 0 or end == top_speed:
        buffer = 0.1
    else:
        buffer = 0
    if end > start:
        keyboard.press("w")
        sleep(100 / top_speed * throttle_change_speed * (end - start) + buffer)
        keyboard.release("w")
    elif end < start:
        keyboard.press("s")
        sleep(100 / top_speed * throttle_change_speed * (start - end) + buffer)
        keyboard.release("s")
