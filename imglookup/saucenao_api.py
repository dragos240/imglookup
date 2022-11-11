from io import BytesIO
from time import sleep
from typing import Iterator, List, Dict
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
from .types.saucenao import (SaucenaoResponse,
                             SaucenaoResult)
from .types.e621 import E621Result


API_URL = "https://saucenao.com/search.php"
SIMILARITY_THRESHOLD = 60.0
MAX_FETCH_ATTEMPTS = 3


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

    def load_json_data(self, path: str) -> SaucenaoResponse:
        with open(path, 'r') as f:
            response = json.loads(
                f.read(), object_hook=SaucenaoResponse.from_json)
            return response

    def fetch_response(self,
                       path: str,
                       store_json: bool = False) -> SaucenaoResponse:
        """Handles the REST response, returns the header and results"""
        if path.endswith('.json'):
            return self.load_json_data(path)
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
            response = json.loads(
                r.text, object_hook=SaucenaoResponse.from_json)
            return response
        raise Exception("Out of attempts.")

    def get_post_ids(self,
                     paths: List[str],
                     args: Namespace) -> Dict[str, List[int]]:
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
                response = self.fetch_response(path, args.store_json)

                # Handle API stuff
                user_id: int = response.header.user_id
                status: int = response.header.status
                if user_id > 0:
                    if status > 0:
                        warn("Index resolution error.")
                    elif status < 0:
                        raise ApiError("Bad image or other request error.")
                else:
                    raise ApiError("API did not respond. Cannot continue.")

                # Handle results
                results = list(filter(filter_func, response.results))
                results.sort(key=sort_func)
                if len(results) == 0:
                    warn("No close matches for", path)
                    continue
                # TODO: Check for sources other than e621
                for result in results:
                    try:
                        post_id: int = result.data.e621_id
                        post_ids.append(post_id)
                    except KeyError:
                        verb("KeyError. Continuing")
                        verb("json_data:", result.to_json())
                        continue
                files[path] = post_ids
        except ApiError as e:
            err("ApiError occurred", error=e)
        except Exception as e:
            err("Other error encountered:", error=e)

        return files


def sort_func(result: SaucenaoResult):
    """Sort by similarity"""
    return SIMILARITY_THRESHOLD - float(result.header.similarity)


def filter_func(result: SaucenaoResult):
    """Return True if `similarity` is greater than the threshold"""
    return float(result.header.similarity) > SIMILARITY_THRESHOLD


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
