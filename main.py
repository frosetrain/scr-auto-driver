import logging
from os import system
from threading import Event
from time import sleep, time

from Levenshtein import distance as lev_distance
from PIL import ImageGrab
from pynput.keyboard import Controller
from pynput.mouse import Button, Listener
from pytesseract import image_to_string

window = (0, 100, 1920, 1180)
speed_limit_bbox = (window[0] + 865, window[1] + 940, window[0] + 925, window[1] + 980)
signal_bbox = (window[0] + 1685, window[1] + 893, window[0] + 1686, window[1] + 1040)
signal_points = ((0, 0), (0, 49), (0, 98), (0, 146))
aws_bbox = (window[0] + 1430, window[1] + 960, window[0] + 1431, window[1] + 961)
distance_bbox = (window[0] + 350, window[1] + 1023, window[0] + 426, window[1] + 1068)
station_name_bbox = (
    window[0] + 186,
    window[1] + 918,
    window[0] + 777,
    window[1] + 1008,
)
top_speed = 100
throttle_change_speed = 0.0334


class Station:
    def __init__(self, name, brake, time1, time2, time3):
        self.name = name
        self.brake = brake
        self.time1 = time1  # entry speed to 20
        self.time2 = time2  # 20 to 5
        self.time3 = time3  # 5 to 0


nb_stations = [
    Station("Stepford East", 0.17, 6.654160023, 3.992200136, 3.088099957),
    Station("Stepford High Street", 0.1, 4.555209875, 4.76011014, 3.024209976),
    Station("Whitefield Lido", 0.1, 2.4088099, 5.13623023, 2.759949923),
    Station("Stepford United Football", 0.1, 4.232980013, 1.559949875, 0.6961500645),
]
sb_stations = [
    Station("Stepford United Football", 0.1, 3.181479931, 4.375799894, 3.936160088),
    Station("Whitefield Lido", 0.12, 3.149699926, 2.848060131, 7.200239897),
    Station("Stepford High Street", 0.1, 4.90790987, 3.744009972, 6.296169996),
    Station("Stepford East", 0.1, 6.793120146, 4.768109798, 3.752220154),
    Station("Stepford Central", 0.1, 8.626450062, 3.343790054, 3.65602994),
]
nb_station_names = [station.name for station in nb_stations]
sb_station_names = [station.name for station in sb_stations]

keyboard = Controller()
logging.getLogger("PIL.TiffImagePlugin").setLevel(logging.INFO)
# logging.basicConfig(filename="scr.log", encoding="utf-8", level="INFO")
logging.basicConfig(level="DEBUG")


def get_speed_limit() -> int:
    pic = ImageGrab.grab(bbox=speed_limit_bbox)
    pic = pic.resize((90, 60))
    pic.save("speed_limit.tif")
    speed_limit = image_to_string("speed_limit.tif", config="--psm 7 digits get.images")
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
    distance = image_to_string("distance.tif", config="--psm 7 digits get.images")
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
    if pixels[0, 0][0] > 180:
        keyboard.press("q")
        keyboard.release("q")
        logging.debug("AWS")


def change_throttle(start, end) -> None:
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


def get_station_name() -> str:
    pic = ImageGrab.grab(bbox=station_name_bbox)
    pic.save("station.tif")
    return image_to_string("station.tif").strip()


def on_click_1(x, y, button, pressed):
    if pressed and button == Button.left:
        logging.info(time())
        change_throttle(current_target_speed, 20)
        return False


def on_click_2(x, y, button, pressed):
    if pressed and button == Button.left:
        logging.info(time())
        change_throttle(20, 5)
        return False


def on_click_3(x, y, button, pressed):
    if pressed and button == Button.left:
        logging.info(time())
        change_throttle(5, 0)
        return False


def station_stop(station: Station) -> None:
    logging.debug(station.name)
    reached = False
    while not reached:
        distance = get_station_distance()
        if distance == 0.0:
            reached = True

    logging.info(time())

    # with Listener(on_click=on_click_1) as listener:
        # listener.join()
    # with Listener(on_click=on_click_2) as listener:
        # listener.join()
    # with Listener(on_click=on_click_3) as listener:
        # listener.join()
    sleep(station.time1)
    change_throttle(current_target_speed, 20)
    sleep(station.time2)
    change_throttle(20, 5)
    sleep(station.time3)
    change_throttle(5, 0)
    keyboard.press("t")
    keyboard.release("t")
    done = False
    while not done:
        distance = get_station_distance()
        if distance != 0.0:
            done = True


if __name__ == "__main__":
    current_target_speed = 0
    sleep(2)
    direction = "sb"
    station = sb_stations[0]
    while True:
        # Read values from screen
        speed_limit = get_speed_limit()
        signal_limit = get_signal_limit()
        station_distance = get_station_distance()
        if station_distance < 0.03:
            # This function skips the speed limit and signal,
            # and makes the train stop at the station correctly.
            # The main loop continues once the stop is complete.
            station_stop(station)

            # Get the next station
            station_name = get_station_name()
            closest_lev = lev_distance(station_name, sb_station_names[0])
            closest_name = sb_station_names[0]
            for this in sb_station_names:
                lev = lev_distance(station_name, this)
                if lev < closest_lev:
                    closest_lev = lev
                    closest_name = this
            logging.debug(f"Next station: {closest_name}")
            if direction == "sb":
                station = sb_stations[sb_station_names.index(closest_name)]
            else:
                station = nb_stations[nb_station_names.index(closest_name)]

            if direction == "nb" and station.name == "Stepford United Football":
                terminus = True
            elif station.name == "Stepford Central":
                terminus = True

            current_target_speed = 0
            continue

        elif station_distance < station.brake:
            station_limit = 45
        else:
            station_limit = top_speed

        new_target_speed = min(speed_limit, signal_limit, station_limit)

        # Change the throttle
        if new_target_speed != current_target_speed:
            logging.debug(f"Changing speed to {new_target_speed}")
            change_throttle(current_target_speed, new_target_speed)
            current_target_speed = new_target_speed

        # handle_aws()

        system("clear")
        logging.debug(f"Speed limit: {speed_limit}")
        logging.debug(f"Signal limit: {signal_limit}")
        logging.debug(f"Distance to station: {station_distance}")
        logging.debug(f"Station limit: {station_limit}")
        logging.debug(f"Target speed: {new_target_speed}")
