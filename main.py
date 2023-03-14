import logging
from os import system
from threading import Event
from time import sleep

import pytesseract
from PIL import ImageGrab
from pynput.keyboard import Controller

window = (0, 100, 1920, 1180)
speed_limit_bbox = (window[0] + 865, window[1] + 940, window[0] + 925, window[1] + 980)
signal_bbox = (window[0] + 1685, window[1] + 893, window[0] + 1686, window[1] + 1040)
signal_points = ((0, 0), (0, 49), (0, 98), (0, 146))
aws_bbox = (window[0] + 1430, window[1] + 960, window[0] + 1431, window[1] + 961)
distance_bbox = (window[0] + 350, window[1] + 1023, window[0] + 426, window[1] + 1068)
top_speed = 100
throttle_change_speed = 0.0337

keyboard = Controller()

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
        return speed_limit
    except ValueError:
        logging.debug(f"Tesseract error: {speed_limit}")
        return top_speed


def get_signal_limit() -> int:
    pic = ImageGrab.grab(bbox=signal_bbox)
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
        signal_limit = top_speed

    return signal_limit


def get_station_distance() -> float:
    pic = ImageGrab.grab(bbox=distance_bbox)
    pic.save("distance.tif")
    distance = pytesseract.image_to_string(
        "distance.tif", config="--psm 7 digits get.images"
    )
    distance = distance.strip()
    try:
        distance = float(distance)
    except ValueError:
        distance = 1.0
        logging.debug(f"Tesseract error: {distance}")
    return distance


def handle_aws() -> None:
    pic = ImageGrab.grab(bbox=aws_bbox)
    pixels = pic.load()
    if pixels[0, 0][0] > 200:
        keyboard.press("q")
        logging.debug("AWS")


def change_throttle(start, end):
    if end == 0 or end == top_speed:
        buffer = 0.1
    else:
        buffer = 0
    if end > start:
        keyboard.press("w")
        Event().wait(100 / top_speed * throttle_change_speed * (end - start) + buffer)
        keyboard.release("w")
    elif end < start:
        keyboard.press("s")
        Event().wait(100 / top_speed * throttle_change_speed * (start - end) + buffer)
        keyboard.release("s")


class Station:
    def __init__(self, name, time1, time2, time3):
        self.name = name
        self.time1 = time1  # entry speed to 20
        self.time2 = time2  # 20 to 5
        self.time3 = time3  # 5 to 0


nb_stations = [
    Station("Stepford East", 0, 0, 0),
    Station("Stepford High Street", 0, 0, 0),
    Station("Whitefield Lido", 0, 0, 0),
    Station("Stepford United Football Club", 0, 0, 0),
]
sb_stations = [
    Station("Stepford United Football Club", 0, 0, 0),
    Station("Whitefield Lido", 0, 0, 0),
    Station("Stepford High Street", 0, 0, 0),
    Station("Stepford East", 0, 0, 0),
    Station("Stepford Central", 0, 0, 0),
]
station_names = [station.name for station in stations]


def station_stop(current_target_speed):
    # Get station name
    station_name = "Whitefield Lido"  # TODO: Use Tesseract to obtain this
    station = stations[station_names.index(station_name)]
    reached = False
    while not reached:
        distance = get_station_distance()
        if distance == 0.0:
            reached = True
    sleep(station.time1)
    change_throttle(current_target_speed, 20)
    sleep(station.time2)
    change_throttle(20, 5)
    sleep(station.time3)
    change_throttle(5, 0)


if __name__ == "__main__":
    current_target_speed = 0
    sleep(2)
    while True:
        # Read values from screen
        speed_limit = get_speed_limit()
        signal_limit = get_signal_limit()
        station_distance = get_station_distance()
        if station_distance < 0.14:
            station_limit = 45
        if station_distance < 0.03:
            station_stop()
            # This function skips the speed limit and signal,
            # and makes the train stop at the station correctly.
            # The main loop continues once the stop is complete.
            current_target_speed = 0
            continue
        else:
            station_limit = top_speed

        new_target_speed = min(speed_limit, signal_limit, station_limit)

        # Change the throttle
        if new_target_speed != current_target_speed:
            logging.info(f"Changing speed to {new_target_speed}")
            change_throttle(current_target_speed, new_target_speed)
            current_target_speed = new_target_speed

        handle_aws()

        system("clear")
        logging.debug(f"Speed limit: {speed_limit}")
        logging.debug(f"Signal limit: {signal_limit}")
        logging.debug(f"Distance to station: {station_distance}")
        logging.debug(f"Station limit: {station_limit}")
        logging.debug(f"Target speed: {new_target_speed}")

        # sleep(0.5)
