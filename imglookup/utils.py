from os import walk
from os.path import (normpath,
                     join as path_join,
                     dirname,
                     basename,
                     isdir)

verbose = False


def init_logger(args):
    """sets verbose var"""
    global verbose
    verbose = args.verbose


def verbose(*msg):
    if verbose:
        print("VERB:", *msg)


def warn(*msg):
    print("WARN:", *msg)


def err(*msg, error=None):
    msg = " ".join(msg)
    if error is None:
        raise Exception(f"ERR: {msg}")
        return
    print("ERR:", *msg)
    raise error


def get_recursive_images(dirpath: str) -> list[str]:
    """Return list of images within a directory"""
    paths = []
    for idx, (root, dirs, files) in enumerate(walk(dirpath)):
        for file in files:
            ext = file.split('.')[-1].lower()
            if ext not in ('jpg', 'jpeg', 'png', 'gif'):
                continue
            paths.append(normpath(path_join(root, file)))
        if idx == 3:
            break

    return paths


def get_path_components(path: str) -> (str, str, str):
    """Returns a tuple of (RELATIVE_DIR_PATH, FILE_NAME, FILE_EXT)"""
    dir_path = dirname(path)
    file_name = basename(path)
    _, file_ext = file_name.split('.')

    return dir_path, file_name, file_ext


def get_base_dirs(root_path: str,
                  base_dir: str) -> (str, str):
    """Returns a tuple of (ORIGINAL_BASE_DIR, NEW_BASE_DIR)"""
    original_base_dir = dirname(root_path)
    base_dirs = [original_base_dir, original_base_dir]
    if isdir(root_path):
        original_base_dir = root_path
    if base_dir is not None:
        base_dirs[1] = base_dir

    return base_dirs
