import os

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
    print("ERR:", msg)
    raise error


def get_recursive_images(dirpath):
    paths = []
    for idx, (root, dirs, files) in enumerate(os.walk(dirpath)):
        for file in files:
            ext = file.split('.')[-1].lower()
            if ext not in ('jpg', 'jpeg', 'png', 'gif'):
                continue
            paths.append(os.path.join(root, file))
        if idx == 3:
            break
    return paths
