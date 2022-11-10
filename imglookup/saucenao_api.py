from io import BytesIO
from time import sleep
from typing import Iterator, List, Tuple, Dict
from urllib import parse
from contextlib import contextmanager
from os import environ
from os.path import exists
import json
from argparse import Namespace

import requests
from PIL import Image
from dotenv import load_dotenv

from .utils import (verb,
                    err,
                    warn)
from .api import Api, ApiError, DBType


API_URL = "https://saucenao.com/search.php"


class SauceNaoApi(Api):
    def __init__(self):
        super().__init__()
        self.api_key = environ['saucenao_api_key']
        kvs = {
            'api_key': self.api_key,
            'db': DBType.E621,
            'output_type': 2,
            'testmode': True,
            'numres': 4
        }
        self.url = API_URL + parse.urlencode(kvs)

    def get_results(self):
        pass

    def fetch_response(self,
                       path: str,
                       store_json: bool = False) -> Tuple[dict, dict]:
        """Handles the REST response, returns the header and results"""
        if path.endswith('.json'):
            with open(path, 'r') as f:
                res = json.loads(f.read())
                return res['header'], res['results']
        file_ext = path.split('.')[-1]
        files = {}
        # Use a thumbnail instead of base image to reduce bandwidth for very
        # large images
        with get_thumbnail(path) as image_data:
            files['file'] = (f'image.{file_ext}', image_data.getvalue())

        for _ in range(MAX_FETCH_ATTEMPTS):
            r = requests.post(self.url, files=files)
            if r.status_code != 200:
                if r.status_code == 403:
                    raise ApiError("Invalid API key")
                warn("Sleeping for 10s after status code:",
                     r.status_code)
                sleep(10)
                continue

            # If `store_json` is set, save the resulting JSON for later parsing
            if store_json:
                with open('debug-saucenao.json', 'w') as f:
                    f.write(r.text)
            res = json.loads(r.text)
            return res['header'], res['results']
        raise Exception("Out of attempts.")


SIMILARITY_THRESHOLD = 60.0
MAX_FETCH_ATTEMPTS = 3


def sort_func(e):
    """Sort by similarity"""
    return SIMILARITY_THRESHOLD - float(e['header']['similarity'])


def filter_func(e):
    """Return True if `similarity` is greater than the threshold"""
    return float(e['header']['similarity']) > SIMILARITY_THRESHOLD


def get_post_ids(paths: List[str],
                 args: Namespace) -> Dict[str, List[str]]:
    """Gets post IDs for each path"""
    files = {}
    if not paths and args.saucenao:
        paths = [args.saucenao]
    try:
        for path in paths:
            if exists(path + '.json'):
                print(f"Tag file exists for {path}, skipping...")
                continue
            print(f"Beginning parse for {path}...")
            post_ids = []
            header, results = fetch_response(path, args.store_json)

            # Handle API stuff
            user_id = int(header['user_id'])
            status = int(header['status'])
            if user_id > 0:
                if status > 0:
                    warn("Index resolution error.")
                elif status < 0:
                    raise ApiError("Bad image or other request error.")
            else:
                raise ApiError("API did not respond. Cannot continue.")

            # Handle results
            results = list(filter(filter_func, results))
            results.sort(key=sort_func)
            if len(results) == 0:
                warn("No close matches for", path)
                continue
            for idx, result in enumerate(results):
                try:
                    post_id = result['data']['e621_id']
                    post_ids.append(post_id)
                except KeyError:
                    verb("KeyError. Continuing")
                    verb("json_data:", result['data'])
                    continue
            files[path] = post_ids
    except ApiError as e:
        err("ApiError occurred", error=e)
    except Exception as e:
        err("Other error encountered:", error=e)

    return files


@contextmanager
def get_thumbnail(path: str) -> Iterator[BytesIO]:
    """Returns a contextmanager which yields thumbnail data"""
    file_format = get_format_type(path)

    image = Image.open(path)
    image = image.convert('RGB')
    width, height = image.size
    aspect_ratio = width / height
    if width > 512:
        image.thumbnail((512, 512 * aspect_ratio))
    image_data = BytesIO()
    image.save(image_data, format=file_format)
    try:
        yield image_data
    finally:
        image_data.close()


def get_format_type(path) -> str:
    """Gets the format type for a file"""
    file_format: str = path.split('.')[-1].upper()
    if file_format == "JPG":
        file_format = "JPEG"

    return file_format
