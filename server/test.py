import sys
import traceback

from server import config, setup
from utils import file_utils

from utils.logger import get_logger
from repo.git_tracker import GitTracker
from repo.svn_tracker import SvnTracker

logger = get_logger(__name__)


def setup_folders():
    logger.info("Creating patch directories")
    folders = [config.patches_dir, config.tracker_dir]

    for fol in folders:
        logger.info(f"Creating folder: {fol}")
        file_utils.create_folders(fol)

    for sync_config in config.sync_configs:
        file_utils.create_folders(f"{config.patches_dir}{sync_config['name']}/")


def test_diffs(svn: SvnTracker, git: GitTracker):
    from utils import diff_tools

    logger.info("Running tests")
    # svn2 = SvnTracker(svn.name, "C:\svnrepo-test", "test")
    #
    # # Test revision diff for git->svn
    # rev = "f3bfa66481684b27a129d6886b1881b1d44f3c9e"
    # msg, author, diff, files = git.get_diff(rev)
    # path, fdiff = svn.format_and_save(rev, diff)
    # files = diff_tools.git_get_binary_files(fdiff)
    # print(", ".join(files))
    # for file in files:
    #     file_byte_array = git.run_command("git", ["show", "--binary", f"{rev}:{file}"], return_binary=True)
    #     # print(codecs.decode(file_byte_array))
    # svn2.apply(rev, diff, git)

    # # Test revision diff for svn->git
    # rev = "37267"
    # msg, author, diff, files = svn.get_diff(rev)
    # path, fdiff = git.format_and_save(rev, diff)
    # files = diff_tools.git_get_binary_files(fdiff)
    # print(", ".join(files))
    # for file in files:
    #     file_byte_array = svn.repo.cat(file, rev)
    #     print(codecs.decode(file_byte_array))

    # Test revision diff for git->svn
    rev = "d19be7a46d5b9742105ef59dcbe834fd1ed4c288"
    date, msg, author, diff, files = git.get_diff(rev)
    path, fdiff = svn.format_and_save(rev, diff)
    renames = diff_tools.git_get_rename_files(diff)
    print(fdiff)
    print(f"files are: {', '.join(map(lambda x: x['to'], renames))}")


if __name__ == '__main__':
    try:
        # setup
        setup.run()
        file_utils.create_folders(f"{config.patches_dir}test/")

        # init trackers
        svn_tracker = SvnTracker("test", "c:/svnrepo", "trunk", is_test=True)
        git_tracker = GitTracker("test", "c:/gitrepo", "trunk", is_test=True)

        # run test simulations
        test_diffs(svn_tracker, git_tracker)

    except KeyboardInterrupt:
        logger.info("Stopped!")
        raise
    except Exception as ex:
        logger.info(ex)
        traceback.print_exc(file=sys.stdout)
        sys.exit(1)
