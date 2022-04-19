import json
import random
import requests
from PIL import Image
from io import BytesIO

jsonFile = open("tweets.json", "r")
tweetsJSON = jsonFile.read()
json_dict = json.loads(tweetsJSON)
jsonFile.close()


def get_tweet_image():
    random_index = random.randrange(0, len(json_dict['tweets']) - 1)
    tweet = json_dict['tweets'][random_index]['url']
    response = requests.get(tweet)
    return Image.open(BytesIO(response.content))
