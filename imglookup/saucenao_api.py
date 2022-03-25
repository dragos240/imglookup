from io import BytesIO
from time import sleep
from urllib import parse
from contextlib import contextmanager
from os import getenv
import json
from argparse import Namespace

import requests
from PIL import Image
from dotenv import load_dotenv

from .utils import (verbose,
                    err,
                    warn)

load_dotenv()

api_key = getenv('saucenao_api_key')
debug_url = "http://127.0.0.1:5000/"


class ApiError(Exception):
    """For SauceNao API/Index issues"""
    pass


class AccountError(Exception):
    """For SauceNao account issues (like limits)"""
    pass


class DBType:
    GELBOORU = 25
    E621 = 29


url_fmt = "https://saucenao.com/search.php?"
kvs = {
    'api_key': api_key,
    'db': DBType.E621,
    'output_type': 2,
    'testmode': True,
    'numres': 4
}
url = url_fmt + parse.urlencode(kvs)


def sort_func(e):
    return 85 - float(e['header']['similarity'])


def filter_func(e):
    return float(e['header']['similarity']) > 85.0


def get_post_ids(paths: list[str],
                 args: Namespace) -> dict[str, list[str]]:
    """Gets post IDs from paths"""
    files = {}
    if not paths and args.saucenao:
        paths = [args.saucenao]
    try:
        for path in paths:
            post_ids = []
            header, results = fetch_response(path, args.store_json)

            # Handle API stuff
            user_id = int(header['user_id'])
            status = int(header['status'])
            if user_id > 0:
                verbose("User ID is valid")
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
                    verbose("KeyError. Continuing")
                    verbose("json_data:", result['data'])
                    continue
            files[path] = post_ids
    except ApiError as e:
        err("ApiError occurred", error=e)
    except AccountError as e:
        err("AccountError occurred", error=e)
    except Exception as e:
        err("Other error encountered:", error=e)

    return files


def fetch_response(path: str, store_json: bool) -> (dict, dict):
    """Handles the REST response, returns the header and results"""
    if path.endswith('.json'):
        with open(path, 'r') as f:
            res = json.loads(f.read())
            return res['header'], res['results']
    file_ext = path.split('.')[-1]
    files = {}
    with get_thumbnail(path) as image_data:
        files['file'] = (f'image.{file_ext}', image_data.getvalue())

    for _ in range(3):
        r = requests.post(url, files=files)
        if r.status_code != 200:
            if r.status_code == 403:
                raise ApiError("Invalid API key")
            warn("Sleeping for 10s after status code:",
                 r.status_code)
            sleep(10)
            continue

        if store_json:
            with open('debug-saucenao.json', 'w') as f:
                f.write(r.text)
        res = json.loads(r.text)
        return res['header'], res['results']
    raise Exception("Out of attempts.")


@contextmanager
def get_thumbnail(path: str) -> BytesIO:
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
