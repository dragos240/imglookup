import json
from typing import List
from os import getenv
from argparse import Namespace

import requests
from dotenv import load_dotenv

from .utils import err
from .types.data import JsonData

load_dotenv()

username = getenv('e621_username')
api_key = getenv('e621_api_key')

URL_FMT = "https://e621.net/posts/{}.json"


class SaucenaoE621Result(JsonData):
    ext_urls: List[str]
    e621_id: int
    creator: str
    material: str
    characters: str

    def __init__(self,
                 ext_urls,
                 e621_id,
                 creator,
                 material,
                 characters):
        self.ext_urls = ext_urls
        self.e621_id = e621_id
        self.creator = creator
        self.material = material
        self.characters = characters


def get_tags(post_id: str, args: Namespace) -> dict[str, list[str]]:
    """Get tags in format {CATEGORY: [tag1, ... tagN]}"""
    # TODO: Make this more generic so it returns the tags in list format
    store_json = args.store_json
    e621_json = args.e621
    if e621_json is not None:
        with open(e621_json, 'r') as f:
            tags = parse_json(f.read())
            return tags
    url = URL_FMT.format(post_id)

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
