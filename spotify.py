import six
import sys
import base64
import requests
from PIL import Image
from io import BytesIO

try:
    import sonos_settings
except ImportError:
    sys.exit(1)

TOKEN_ENDPOINT = 'https://accounts.spotify.com/api/token'
NOW_PLAYING_ENDPOINT = 'https://api.spotify.com/v1/me/player/currently-playing'


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
    if response.status_code == 204:
        return {'is_playing': False}
    return response.json()


def get_album():
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
