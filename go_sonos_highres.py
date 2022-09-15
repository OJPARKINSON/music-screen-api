"""
This file is for use with the Pimoroni HyperPixel 4.0 Square (Non Touch) High Res display
it integrates with your local Sonos sytem to display what is currently playing
"""
import asyncio
import sys
import base64
import six
import requests
import random
import json

from PIL import ImageFile, Image
from io import BytesIO
from display_controller import DisplayController, SonosDisplaySetupError


try:
    import utils
    from spotify import get_album
    from twitter import get_tweet_image
    import sonos_settings
except ImportError:
    sys.exit(1)

ImageFile.LOAD_TRUNCATED_IMAGES = True
TOKEN_ENDPOINT = 'https://accounts.spotify.com/api/token'
NOW_PLAYING_ENDPOINT = 'https://api.spotify.com/v1/me/player/currently-playing'

jsonFile = open("tweets.json", "r")
tweetsJSON = jsonFile.read()
json_dict = json.loads(tweetsJSON)

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
    print(response)
    return response.json()

def get_tweet_image(tweetIndex):
    random_index = random.randrange(0, len(json_dict['tweets']) - 1)
    tweet = json_dict['tweets'][tweetIndex]['url']
    print(tweet)
    print(tweetIndex)
    response = requests.get(tweet)
    return Image.open(BytesIO(response.content))


def get_image():
    data = get_currently_playing_track()
    if data['is_playing'] == True and data['currently_playing_type'] == 'track':
        image = data['item']['album']['images'][0]['url']
        response = requests.get(image)
        return Image.open(BytesIO(response.content))
    else:
        return None


async def main(loop):
    utils.setup_logging()

    try:
        display = DisplayController(loop, False, False, False, True, False)
    except SonosDisplaySetupError:
        loop.stop()
        return

    tweetIndex = 0
    while True:
        image = get_image()
        if image:
            display.update(image)
            await asyncio.sleep(4)
        else:
            tweetImage = get_tweet_image(tweetIndex)
            display.update(tweetImage)
            tweetIndex+=1
            if tweetIndex == len(json_dict['tweets']): 
                tweetIndex = 0
            await asyncio.sleep(5)

# made a loop to review all the images, I need to add some code to look at the aspect ratio and this code needs cleaning up

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    try:
        loop.create_task(main(loop))
        loop.run_forever()
    finally:
        loop.close()
