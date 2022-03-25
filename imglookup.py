#!/usr/bin/python3

from os.path import (join as path_join,
                     isdir,
                     normpath,
                     exists)
from os import mkdir, rename, remove
from argparse import ArgumentParser
from shutil import copyfile
import json

from imglookup.saucenao_api import get_post_ids
from imglookup.e621_api import get_tags
from imglookup.utils import (init_logger,
                             verbose,
                             get_recursive_images,
                             get_path_components,
                             get_base_dirs)


def main(args):
    init_logger(args)
    paths = [args.path]
    if args.path and isdir(args.path):
        paths = get_recursive_images(args.path)
    elif not args.path:
        paths = None
    src_base_dir = None
    dst_base_dir = None

    file_sets = get_post_ids(paths, args)
    # {file_path: [post_id1, post_id2, ...]}
    for src_file_path, post_ids in file_sets.items():
        if src_base_dir is None:
            src_base_dir, dst_base_dir = \
                get_base_dirs(src_file_path, args.base_dir)
        file_tags = {}
        for post_id in post_ids:
            file_tags[post_id] = get_tags(post_id, args)
        if len(post_ids) == 1:
            post_id = post_ids[0]
            tags = []
            artists = ['unknown_artist']
            for category, tag_list in file_tags[post_id].items():
                if category != 'artist':
                    tags.extend(tag_list)
                    continue
                artists = []
                for artist in tag_list:
                    if artist.endswith('_(artist)'):
                        artist = artist.replace('_(artist)', '')
                    artists.append(artist)
            src_dir_path, _, file_ext = \
                get_path_components(src_file_path)

            # Make dst_dir_path use dst_base_dir
            dst_dir_path = normpath(src_dir_path
                                    .replace(src_base_dir, dst_base_dir))
            sep = '\n      '
            verbose(f'src_file_path: {src_file_path},{sep}'
                    f'src_base_dir: {src_base_dir},{sep}'
                    f'dst_base_dir: {dst_base_dir},{sep}'
                    f'src_dir_path: {src_dir_path},{sep}'
                    f'dst_dir_path: {dst_dir_path},')
            if not exists(dst_dir_path):
                mkdir(dst_dir_path)

            # Rename or copy (in case of --base-dir being set) file
            # Format: ARTISTS-POST_ID.EXT
            new_name = f'{"-".join(artists)}-{post_id}.{file_ext}'
            dst_file_path = path_join(dst_dir_path, new_name)
            src_dir_path = normpath(src_dir_path)
            if src_dir_path == dst_dir_path:
                verbose(f"{src_dir_path} and {dst_dir_path} match")
                if exists(dst_file_path):
                    remove(dst_file_path)
                rename(src_file_path, dst_file_path)
            else:
                verbose(f"{src_dir_path} and {dst_dir_path} do not match")
                copyfile(src_file_path, dst_file_path)

            # Create tags JSON
            json_path = dst_file_path + '.json'
            with open(json_path, 'w') as f:
                f.write(json.dumps(tags))
            verbose(f'Tags written to {json_path}')


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("path",
                        type=str,
                        help="Path(s) to image(s) "
                             "(use empty string if debugging)")
    parser.add_argument("-s", "--store-json",
                        action="store_true",
                        help="Saves JSON responses from APIs")
    parser.add_argument("-b", "--base-dir",
                        type=str,
                        help="Alternative base directory for output files")
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
