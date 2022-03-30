import json
from os import getenv
from argparse import Namespace

import requests
from dotenv import load_dotenv

from imglookup.utils import err

load_dotenv()

username = getenv('e621_username')
api_key = getenv('e621_api_key')

base_url = "https://e621.net/posts/{}.json"


def get_tags(post_id: str, args: Namespace) -> dict[str, list[str]]:
    """Get tags in format {CATEGORY: [tag1, ... tagN]}"""
    # TODO: Make this more generic so it returns the tags in list format
    store_json = args.store_json
    e621_json = args.e621
    if e621_json is not None:
        with open(e621_json, 'r') as f:
            tags = parse_json(f.read())
            return tags
    url = base_url.format(post_id)

    session = requests.Session()
    session.auth = (username, api_key)

    user_agent = f"tag-parser by dragos240 (under user '{username}') 0.1.0"
    headers = {'User-Agent': user_agent}

    try:
        res = session.get(url, headers=headers)
    except Exception as e:
        err("Could not get e621 post", e)
    if store_json:
        with open('debug-e621.json', 'w') as f:
            f.write(res.text)
    tags = parse_json(res.text)

    return tags


def parse_json(text: str):
    """Load the JSON and return the tags"""
    data = json.loads(text)
    tags_block = data['post']['tags']

    return tags_block
