from typing import List, NamedTuple

from server import config

from utils import file_utils

from repo.git_tracker import TrackerBase
from repo.git_tracker import GitTracker
from repo.svn_tracker import SvnTracker

from utils.logger import get_logger

logger = get_logger(__name__)


class TrackerSetup(NamedTuple):
    name: str
    mode: str
    src: TrackerBase
    tgt: TrackerBase


def get_trackers(**kwargs) -> List[TrackerSetup]:
    """use sync configs to create svn/git watchers"""
    trackers: List[TrackerSetup] = []
    # use sync configs to create svn/git watchers
    for sync in config.sync_configs:
        sync_name = sync['name']
        if file_utils.is_git_to_svn_mode(sync['mode']):
            src = GitTracker(sync_name, sync['source_url'], sync['source_branch'], **kwargs)
            tgt = SvnTracker(sync_name, sync['target_url'], sync['target_branch'], **kwargs)
            trackers.append(TrackerSetup(sync_name, sync['mode'], src, tgt))

        elif file_utils.is_svn_to_git_mode(sync['mode']):
            src = SvnTracker(sync_name, sync['source_url'], sync['source_branch'], **kwargs)
            tgt = GitTracker(sync_name, sync['target_url'], sync['target_branch'], **kwargs)
            trackers.append(TrackerSetup(sync_name, sync['mode'], src, tgt))

    return trackers


def setup_folders():
    logger.info("Creating patch directories")
    folders = [config.patches_dir, config.tracker_dir]

    for fol in folders:
        logger.info(f"Creating folder: {fol}")
        file_utils.create_folders(fol)

    for sync_config in config.sync_configs:
        file_utils.create_folders(f"{config.patches_dir}{sync_config['name']}/")


def run():
    setup_folders()
