"""
This file is for use with the Pimoroni HyperPixel 4.0 Square (Non Touch) High Res display
it integrates with your local Sonos sytem to display what is currently playing
"""
import asyncio
import logging
import os
import sys
import requests
import six
import base64
import json
import random

from io import BytesIO
from PIL import Image, ImageFile
from display_controller import DisplayController, SonosDisplaySetupError

_LOGGER = logging.getLogger(__name__)

try:
    import sonos_settings
except ImportError:
    sys.exit(1)

TOKEN_ENDPOINT = 'https://accounts.spotify.com/api/token'
NOW_PLAYING_ENDPOINT = 'https://api.spotify.com/v1/me/player/currently-playing'

ImageFile.LOAD_TRUNCATED_IMAGES = True

jsonFile = open("tweets.json", "r")
tweetsJSON = jsonFile.read()
json_dict = json.loads(tweetsJSON)
jsonFile.close()


def setup_logging():
    """Set up logging facilities for the script."""
    log_level = getattr(sonos_settings, "log_level", logging.INFO)
    log_file = getattr(sonos_settings, "log_file", None)
    if log_file:
        log_path = os.path.expanduser(log_file)
    else:
        log_path = None

    fmt = "%(asctime)s %(levelname)7s - %(message)s"
    logging.basicConfig(format=fmt, level=log_level)

    # Suppress overly verbose logs from libraries that aren't helpful
    logging.getLogger("aiohttp.access").setLevel(logging.WARNING)
    logging.getLogger("PIL.PngImagePlugin").setLevel(logging.WARNING)

    if log_path is None:
        return

    _LOGGER.info("Writing to log file: %s", log_path)
    logfile_handler = logging.FileHandler(log_path, mode="a")

    logfile_handler.setLevel(log_level)
    logfile_handler.setFormatter(logging.Formatter(fmt))

    logger = logging.getLogger("")
    logger.addHandler(logfile_handler)


def redraw(display, image):
    display.update(image)


def get_access_token():
    auth_header = base64.b64encode(
        six.text_type(sonos_settings.client_id + ":" +
                      sonos_settings.client_secret).encode("ascii")
    )
    headers = {
        "Authorization": "Basic %s" % auth_header.decode("ascii"),
        "Content-Type": "application/x-www-form-urlencoded",
    }

    response = requests.post(
        TOKEN_ENDPOINT,
        headers=headers,
        data={
            'grant_type': 'refresh_token',
            'refresh_token': sonos_settings.refresh_token
        }
    )
    return response.json()


def get_currently_playing_track():
    auth_response = get_access_token()
    access_token = auth_response["access_token"]
    headers = {
        'Authorization': 'Bearer ' + access_token,
        'Content-Type': 'application/json'
    }
    response = requests.get(NOW_PLAYING_ENDPOINT, headers=headers)
    return response.json()


def get_tweet_image():
    random_index = random.randrange(0, len(json_dict['tweets']) - 1)
    tweet = json_dict['tweets'][random_index]['url']
    response = requests.get(tweet)
    return Image.open(BytesIO(response.content))


def get_image():
    data = get_currently_playing_track()

    if data['is_playing'] is True:
        if data['currently_playing_type'] == 'episode':
            return Image.open(sys.path[0] + "/tv.png")
        elif data['currently_playing_type'] == 'track':
            image = data['item']['album']['images'][0]['url']
            response = requests.get(image)
            return Image.open(BytesIO(response.content))
    else:
        return None


async def main(loop):
    setup_logging()
    show_details_timeout = getattr(
        sonos_settings, "show_details_timeout", None)
    overlay_text = getattr(sonos_settings, "overlay_text", None)
    show_play_state = getattr(sonos_settings, "show_play_state", None)

    show_details = sonos_settings.show_details
    show_artist_and_album = sonos_settings.show_artist_and_album

    try:
        display = DisplayController(
            loop, show_details, show_artist_and_album, show_details_timeout, overlay_text, show_play_state)
    except SonosDisplaySetupError:
        loop.stop()
        return

    while True:
        image = get_image()
        if image:
            redraw(display, image)
            await asyncio.sleep(4)
        else:
            tweetImage = get_tweet_image()
            redraw(display, tweetImage)
            await asyncio.sleep(60)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    try:
        loop.create_task(main(loop))
        loop.run_forever()
    finally:
        loop.close()
