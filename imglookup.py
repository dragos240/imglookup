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

    # Check if path is a directory, if so, recurse into it
    paths = [args.path]
    if args.path and isdir(args.path):
        paths = get_recursive_images(args.path)
    # If path is missing, we must be debugging
    elif not args.path:
        paths = None

    src_base_dir = None
    dst_base_dir = None

    # Get sets of post ids for each path. One path may have multiple results
    file_sets = get_post_ids(paths, args)
    # {file_path: [post_id1, post_id2, ...]}
    for src_file_path, post_ids in file_sets.items():
        # If we haven't set the source base directory, it must be the first
        # iteration, so use the file path to find the base directory
        if src_base_dir is None:
            src_base_dir, dst_base_dir = \
                get_base_dirs(src_file_path, args.base_dir)

        # For each potential image, get the tags from the booru
        file_tags = {}
        for post_id in post_ids:
            file_tags[post_id] = get_tags(post_id, args)
        # If there's only one close result, use it
        if len(post_ids) == 1:
            post_id = post_ids[0]
            tags = []
            artists = ['unknown_artist']
            # Split the tags from their categories and parse them
            for category, tag_list in file_tags[post_id].items():
                # If the category is not `artist`, add to the main tag list
                # This is used when re-naming the file if `no_rename` is false
                if category != 'artist':
                    tags.extend(tag_list)
                    continue
                # There could be multiple artists, so iterate over them
                artists = []
                for artist in tag_list:
                    # Some artists have tags ending in `_artist()`, remove
                    # the suffix
                    if artist.endswith('_(artist)'):
                        artist = artist.replace('_(artist)', '')
                    artists.append(artist)

            # Split each file name into the base directory, base name
            # (without an extension), and the extension
            src_dir_path, src_file_name_base, file_ext = \
                get_path_components(src_file_path)

            # Replace the root source directory with the base directory and
            # re-base it in case `base_dir` is set
            dst_dir_path = normpath(src_dir_path
                                    .replace(src_base_dir, dst_base_dir))
            # In the case where `base_dir` is set, we may need to create the
            # directory structure, so create if necessary
            if not exists(dst_dir_path):
                mkdir(dst_dir_path)

            # Set destination file path in case `base_dir` is set
            dst_file_path = path_join(dst_dir_path, src_file_name_base)
            # If `no_rename` is false, rename or copy the file (useful when)
            # searching based on artist(s)
            if not args.no_rename:
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

            # Create tags JSON for each file
            json_path = dst_file_path + '.json'
            with open(json_path, 'w') as f:
                f.write(json.dumps(tags, indent=2))
            verbose(f'Tags written to {json_path}')


if __name__ == '__main__':
    # Do the argument parsing in this block
    parser = ArgumentParser()
    parser.add_argument("path",
                        type=str,
                        help="Path(s) to image(s) "
                             "(use empty string if debugging)")
    parser.add_argument("-n", "--no-rename",
                        action="store_true",
                        help="Don't rename the file")
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
