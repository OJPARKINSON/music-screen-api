import json
import requests

try:
    import sonos_settings
except ImportError:
    sys.exit(1)

tweet_URLs = []
pagination_token = None

jsonFile = open("tweets.json", "r")
tweetsJSON = jsonFile.read()
json_dict = json.loads(tweetsJSON)
jsonFile.close()

def parse_tweets(responseJSON):
    for tweet in responseJSON['data']:
        if tweet["author_id"] == sonos_settings.AUTHOR_ID:
            for media in responseJSON['includes']['media']:
                if media["media_key"] == tweet["attachments"]["media_keys"][0] and media["type"] == "photo":
                    print(media)
                    tweet_URLs.append(media["url"])
                    break

    if responseJSON["meta"]["next_token"] is not None:
        return responseJSON["meta"]["next_token"]


def get_tweets(pagination_token):
    parameters = {
        "expansions": "author_id,attachments.media_keys",
        "media.fields": "url",
    }
    if pagination_token is not None:
        parameters["pagination_token"] = pagination_token

    headers = {
        "Authorization": "Bearer " + sonos_settings.TWITTER_API_KEY,
    }

    response = requests.get(
        "https://api.twitter.com/2/users/" + sonos_settings.TWITTER_ID + "/liked_tweets",
        headers=headers,
        params=parameters,
    )

    return response.json(), response.status_code


# Get every page of tweets
while True:
    response, status = get_tweets(pagination_token)
    if status != 200:
        print("Error: " + str(status) + str(response))
        break

    pagination_token = parse_tweets(response)
    if pagination_token is None:
        break

# add the image URLs to the JSON list
for url in tweet_URLs:
    json_dict["tweets"].append({"url": url})

# write the JSON list to a file
jsonFile = open("tweets.json", "w")
new_JSON = json.dumps(json_dict, indent=4)
jsonString = jsonFile.write(new_JSON)
jsonFile.close()
