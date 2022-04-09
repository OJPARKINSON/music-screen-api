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

from io import BytesIO
from aiohttp import ClientError
from PIL import Image, ImageFile

import async_demaster
from display_controller import DisplayController, SonosDisplaySetupError

_LOGGER = logging.getLogger(__name__)

try:
    import sonos_settings
except ImportError:
    _LOGGER.error("ERROR: Config file not found. Copy 'sonos_settings.py.example' to 'sonos_settings.py' before you edit. You can do this with the command: cp sonos_settings.py.example sonos_settings.py")
    sys.exit(1)

###############################################################################
# Global variables and setup
POLLING_INTERVAL = 1
WEBHOOK_INTERVAL = 60
TOKEN_ENDPOINT = 'https://accounts.spotify.com/api/token'
NOW_PLAYING_ENDPOINT = 'https://api.spotify.com/v1/me/player/currently-playing'

ImageFile.LOAD_TRUNCATED_IMAGES = True


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

    log_path_exists = os.path.isfile(log_path)
    log_dir = os.path.dirname(log_path)

    if (log_path_exists and os.access(log_path, os.W_OK)) or (
        not log_path_exists and os.access(log_dir, os.W_OK)
    ):
        _LOGGER.info("Writing to log file: %s", log_path)
        logfile_handler = logging.FileHandler(log_path, mode="a")

        logfile_handler.setLevel(log_level)
        logfile_handler.setFormatter(logging.Formatter(fmt))

        logger = logging.getLogger("")
        logger.addHandler(logfile_handler)
    else:
        _LOGGER.error(
            "Cannot write to %s, check permissions and ensure directory exists", log_path)

# async def get_image_data(session, url):
#     """Return image data from a URL if available."""
#     if not url:
#         return None

#     try:
#         async with session.get(url) as response:
#             content_type = response.headers.get('content-type')
#             if content_type and not content_type.startswith('image/'):
#                 _LOGGER.warning(
#                     "Not a valid image type (%s): %s", content_type, url)
#                 return None
#             return await response.read()
#     except ClientError as err:
#         _LOGGER.warning("Problem connecting to %s [%s]", url, err)
#     except Exception as err:
#         _LOGGER.warning("Image failed to load: %s [%s]", url, err)
#     return None


async def redraw(display, image):
    # def should_sleep():
    #     """Determine if screen should be sleeping."""
    #     if sonos_data.type == "line_in":
    #         return getattr(sonos_settings, "sleep_on_linein", False)
    #     if sonos_data.type == "TV":
    #         return getattr(sonos_settings, "sleep_on_tv", False)

    # if should_sleep():
    #     if display.is_showing:
    #         _LOGGER.debug("Input source is %s, sleeping", sonos_data.type)
    #         display.hide_album()
    #     return

    # # see if something is playing
    # if sonos_data.status == "PLAYING":
    #     if not sonos_data.is_track_new():
    #         # Ensure the album frame is displayed in case the current track was paused, seeked, etc
    #         if not display.is_showing:
    #             display.show_album()
    #         return

    #     # slim down the trackname
    #     if sonos_settings.demaster and sonos_data.type not in ["line_in", "TV"]:
    #         offline = not getattr(
    #             sonos_settings, "demaster_query_cloud", False)
    #         sonos_data.trackname = await async_demaster.strip_name(sonos_data.trackname, session, offline)

    #     image_data = await get_image_data(session, sonos_data.image_uri)
    #     if image_data:
    #         pil_image = Image.open(BytesIO(image_data))
    #     elif sonos_data.type == "line_in":
    #         pil_image = Image.open(sys.path[0] + "/line_in.png")
    #     elif sonos_data.type == "TV":
    #         pil_image = Image.open(sys.path[0] + "/tv.png")

    #     if pil_image is None:
    #         _LOGGER.warning("Image not available, using default")
    display.update(image)

# export const getNowPlaying = async () => {
#   const { access_token } = await getAccessToken();

#   return fetch(NOW_PLAYING_ENDPOINT, {
#     headers: {
#       Authorization: `Bearer ${access_token}`,
#     },
#   });
# };


def get_access_token():
    auth_header = base64.b64encode(
        six.text_type(sonos_settings.client_id + ":" +
                      sonos_settings.client_secret).encode("ascii")
    )
    headers = {
        'Authorization': auth_header,
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    response = requests.post(
        TOKEN_ENDPOINT,
        headers=headers,
        data={
            'grant_type': 'refresh_token',
            'refresh_token': sonos_settings.refresh_token
        }
    )
    print(response.status_code)
    return response.json()


def get_currently_playing_track():
    access_token = get_access_token()
    print(access_token)
    headers = {
        'Authorization': 'Bearer ' + access_token['access_token'],
        'Content-Type': 'application/json'
    }
    response = requests.get(NOW_PLAYING_ENDPOINT, headers=headers)
    return response.json()


def get_image():
    data = get_currently_playing_track()
    print(data)
    if data['item']['album']['images']:
        image = data['item']['album']['images'][0]['url']
        response = requests.get(image)
    else:
        image = None
    return Image.open(BytesIO(response.content))


async def main(loop):
    setup_logging()
    show_details_timeout = getattr(
        sonos_settings, "show_details_timeout", None)
    overlay_text = getattr(sonos_settings, "overlay_text", None)
    show_play_state = getattr(sonos_settings, "show_play_state", None)

    try:
        display = DisplayController(loop, sonos_settings.show_details,
                                    sonos_settings.show_artist_and_album, show_details_timeout, overlay_text, show_play_state)
    except SonosDisplaySetupError:
        loop.stop()
        return

    while True:
        image = get_image()
        await redraw(display, image)
        await asyncio.sleep(2)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    try:
        loop.create_task(main(loop))
        loop.run_forever()
    finally:
        loop.close()
