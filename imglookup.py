#!/usr/bin/python3

import os
from argparse import ArgumentParser

from imglookup.saucenao_api import get_post_ids
from imglookup.e621_api import get_tags
from imglookup.utils import init_logger, verbose, get_recursive_images


def main(args):
    init_logger(args)
    paths = [args.path]
    if args.path and os.path.isdir(args.path):
        paths = get_recursive_images(args.path)
    elif not args.path:
        paths = None

    # {file_path: [post_id1, post_id2, ...]}
    file_sets = get_post_ids(paths, args)
    for file_path, post_ids in file_sets.items():
        file_tags = {}
        for post_id in post_ids:
            file_tags[post_id] = get_tags(post_id, args)
        if len(post_ids) == 1:
            post_id = post_ids[0]
            tags = file_tags[post_id]
            artists = set()
            for tag in tags:
                if tag.endswith('_(artist)'):
                    artist = tag.replace('_(artist)', '')
                    artists.add(artist)
            dir_name = os.path.dirname(file_path)
            file_name = os.path.basename(file_path)
            _, file_ext = file_name.split('.')
            new_name = f'{"-".join(artists)}-{post_id}.{file_ext}'
            new_file_path = os.path.join(dir_name, new_name)
            verbose('new_file_path:', new_file_path)
            # os.rename(file_path, new_file_path)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("path",
                        type=str,
                        help="Path(s) to image(s) "
                             "(use empty string if debugging)")
    parser.add_argument("-s", "--store-json",
                        action="store_true",
                        help="Saves JSON responses from APIs")
    parser.add_argument("--saucenao",
                        type=str,
                        help="Specify saucenao JSON file to parse")
    parser.add_argument("--e621",
                        type=str,
                        help="Specify e621 JSON file to parse")
    parser.add_argument("-v", "--verbose",
                        action="store_true",
                        help="Prints out more verbose messages for debugging")
    args = parser.parse_args()

    try:
        main(args)
    except KeyboardInterrupt:
        pass
