import shutil

from utils import file_utils

from utils.logger import get_logger
from server.config import tracker_dir

logger = get_logger(__name__)


def initialize(name):
    filename = f"{tracker_dir}sync_last_{name}"
    shutil.copy(filename, f"{filename}.bk")


def get_last_revision(name):
    with open(f"{tracker_dir}sync_last_{name}", "r") as infile:
        src_rev, target_rev_and_pos = infile.read().split('=>')
        infile.close()

    if "@" in target_rev_and_pos:
        target_rev, pos = target_rev_and_pos.split('@')
        pos = 0 if not pos else int(pos)
        return src_rev, target_rev, pos

    return src_rev, target_rev_and_pos, 0


def get_last_src_revision(name):
    src_rev, _, __ = get_last_revision(name)

    return src_rev


def get_last_src_position(name):
    _, __, pos = get_last_revision(name)

    return pos


def get_last_target_revision(name):
    _, target_rev, __ = get_last_revision(name)

    return target_rev


def set_last_revision(name, src_rev, target_rev, pos=0):
    logger.info(f"Saving last revision {src_rev} => {target_rev}")
    with open(f"{tracker_dir}sync_last_{name}", "w") as save_file:
        save_file.write(f"{src_rev}=>{target_rev}@{pos}")
        save_file.flush()
        save_file.close()


def save_pending_revisions(name, pending_revs):
    if not pending_revs or len(pending_revs) <= 0:
        print("No revs to write")
        return

    logger.info(f"Writing {len(pending_revs)} revs to 'pending' file")
    with open(f"{tracker_dir}pending_{name}", "w") as pending_file:
        pending_file.write("\n".join(map(str, pending_revs)))
        pending_file.flush()
        pending_file.close()


def get_pending_revisions(name):
    if not name:
        raise Exception("'Name' is required to load revisions")

    revs = []
    pending_file_name = f"{tracker_dir}pending_{name}"
    logger.info(f"Loading '{name}' revs from 'pending' file: {pending_file_name}")

    if file_utils.file_exists(pending_file_name):
        with open(pending_file_name, "r") as pending_file:
            revs = pending_file.readlines()
            pending_file.close()

    return list(map(str.strip, revs))
