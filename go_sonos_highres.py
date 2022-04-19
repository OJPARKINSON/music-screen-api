"""
This file is for use with the Pimoroni HyperPixel 4.0 Square (Non Touch) High Res display
it integrates with your local Sonos sytem to display what is currently playing
"""
import asyncio
import sys

from PIL import ImageFile
from display_controller import DisplayController, SonosDisplaySetupError


try:
    import utils
    from spotify import get_album
    from twitter import get_tweet_image
except ImportError:
    sys.exit(1)

ImageFile.LOAD_TRUNCATED_IMAGES = True


def redraw(display, image):
    display.update(image)


async def main(loop):
    utils.setup_logging()

    try:
        display = DisplayController(loop)
    except SonosDisplaySetupError:
        loop.stop()
        return

    while True:
        album = get_album()
        if album:
            redraw(display, album)
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
