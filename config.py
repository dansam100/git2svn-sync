import os

import utils
from logger import get_logger

logger = get_logger(__name__)

DUMMY_SVN = False
USE_SVN_PATCH_FORMAT = True
USE_PATCH_TOOL_FOR_SVN = False

DUMMY_GIT = False
USE_PATCH_TOOL_FOR_GIT = False

# trigger
USE_TRIGGERS_TO_INITIATE_SYNC = False

# app root
app_root_dir = os.getcwd().replace("\\", "/")

# synchronization mode 'source=>dest'
default_sync_mode = 'git=>svn'

# patches
patches_dir = f"{app_root_dir}/patches/"

# tracker history
tracker_dir = f"{app_root_dir}/history/"

# git settings
git_pull_timeout = 60000

# sync configurations
sync_configs = [
    # {
    #     'mode': "svn=>git",
    #     'name': 'main_svn2git',
    #     'source_url': "C:/svn.test",
    #     'source_branch': "trunk",
    #     'target_url': "C:/git.test",
    #     'target_branch': "SvnGitMirror",
    # },
    # {
    #     'mode': "git=>svn",
    #     'name': 'main_git2svn',
    #     'source_url': "C:/git.test",
    #     'source_branch': "master",
    #     'target_url': "C:/svn.test",
    #     'target_branch': "GitSvnMirror",
    # },
    {
        'mode': "git=>svn",
        'name': 'main_git2svn',
        'source_url': "C:/git",
        'source_branch': "main",
        'target_url': "C:/svn",
        'target_branch': "trunk",
    },
]

logger.info(f"Sys args: USE_PATCH_TOOL={USE_PATCH_TOOL_FOR_GIT}, Git pull timeout: {git_pull_timeout}")
logger.info(f"SVN args: DUMMY_SVN={DUMMY_SVN}, USE_SVN_PATCH_FORMAT={USE_SVN_PATCH_FORMAT}")
logger.info(f"Git args: DUMMY_GIT={DUMMY_GIT}")

for config in sync_configs:
    source = "Git" if utils.is_git_to_svn_mode(config['mode']) else "Svn"
    target = "Git" if utils.is_svn_to_git_mode(config['mode']) else "Svn"

    source_url = config['source_url']
    target_url = config['target_url']

    source_branch = config['source_branch']
    target_branch = config['target_branch']

    logger.info(f"MODE={config['mode']}")
    logger.info(f"Source: {source} repo: {source_url}, branch: {source_branch}")
    logger.info(f"Target: {target} repo: {target_url}, branch: {target_branch}")
