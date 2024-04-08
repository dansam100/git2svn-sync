import os
import patch
import collections
import subprocess
import threading

from utils import file_utils
from git import Repo

from repo.tracker_base import TrackerBase

from utils.diff_tools import git_format_diff, git_get_binary_files
from server.config import COMPANY_DOMAIN
from server.config import git_pull_timeout
from server.config import patches_dir, DUMMY_GIT, USE_PATCH_TOOL_FOR_GIT
from utils.logger import get_logger

logger = get_logger(__name__)


class GitTracker(TrackerBase):
    def __init__(self, name, url, branch, is_test=False, **kwargs):
        TrackerBase.__init__(self, name, "Git", url, **kwargs)
        self.branch = branch
        self.is_test = is_test
        self.repo = Repo(url)
        self._lock = threading.Lock()

        logger.info("GIT version" + str(self.repo.git.version_info))

        if not is_test:
            branch_exists = False
            for ref in self.repo.references:
                if branch == ref.name:
                    self.cleanup()
                    logger.info(f"Checking out branch: {branch}")
                    self.repo.git.checkout(branch)
                    branch_exists = True
                    break
            if not branch_exists:
                self.cleanup()
                logger.info(f"Checking out NEW branch: {branch}")
                self.repo.git.checkout('-t', f"origin/{branch}")

    def run_command(self, subcommand, args=(), encoding="utf-8-sig", return_binary=False):
        try:
            args = [] if len(args) == 0 else args
            cmd = [subcommand] + args
            git_cmd = subprocess.Popen(cmd, stdout=subprocess.PIPE, cwd=f"{self.repo_path}")
            if return_binary:
                return git_cmd.communicate()[0]
            else:
                return git_cmd.communicate()[0].decode(encoding=encoding)
        except Exception as e:
            logger.error(f"Failed while running command {subcommand}", exc_info=e)
            raise e

    def get_last_commit(self, with_pull=True):
        origin = self.repo.remote('origin')

        if with_pull:
            origin.pull(kill_after_timeout=git_pull_timeout)

        last_commit = self.repo.head.commit
        files = self.repo.git.diff("--name-only", f"{last_commit.hexsha}~1..{last_commit.hexsha}")
        c = collections.namedtuple('LogEntry', ['date', 'message', 'revision', 'author', 'changelist'])

        return c(**{'date': last_commit.committed_date, 'revision': last_commit.hexsha,
                    'message': last_commit.message, 'author': last_commit.author,
                    'changelist': files.splitlines(keepends=False) if files else []})

    def get_revisions_since(self, rev):
        cmd = self.repo.git
        rev_str = cmd.rev_list(f"{rev}..HEAD", "--no-merges")

        return reversed(rev_str.splitlines(keepends=False)) if rev_str else []

    def get_diff(self, rev):
        cmd = self.repo.git
        diff = cmd.diff("--no-prefix", "--binary", f"{rev}~1..{rev}")
        files = cmd.diff("--name-only", f"{rev}~1..{rev}")
        msg = cmd.log("--pretty=format:%B", f"{rev}~1..{rev}")
        date = cmd.log("--pretty=format:%ci", f"{rev}~1..{rev}")
        author = cmd.log("--pretty=format:%ae", f"{rev}~1..{rev}")

        logger.debug(f"Diff (revision = {rev})\n\n{diff}")
        logger.debug(f"Files (revision = {rev}, count = {len(files)})\n\n{files}")

        return date, msg, author, diff, files.splitlines(keepends=False) if files else []

    def commit(self, date, msg, author, rev, diff, files=(), src: TrackerBase = None):
        with self._lock:
            if DUMMY_GIT or self.is_test:
                return "dummy_commit", -1

            if self.apply(rev, diff, src, files):
                logger.info(f"{self.name}: patch successful, committing changes for rev: {rev}...")
                username = author if "@" in author else f"{author}@{COMPANY_DOMAIN}"
                commit_msg = f"{msg}\n\n#author:{username}\n\n#Synced from: {rev}"
                self.repo.git.add("-A")
                self.repo.git.commit(f"--author={author}", "-am", commit_msg)
                # self.repo.git.push()
                # self.repo.git.push("--tags")
                commit_info = self.get_last_commit(True)
                logger.info(f"{self.name}: changes committed for rev: {rev}")
                return commit_msg, commit_info.revision
            else:
                return None, None

    def apply(self, rev, diff, src: TrackerBase = None, files: list = ()):
        logger.info(f"Performing 'git apply patch <diff>' for rev: {rev}")
        if DUMMY_GIT:
            return

        patch_path, formatted_diff = self.format_and_save(rev, diff)
        binary_files = git_get_binary_files(formatted_diff)

        if USE_PATCH_TOOL_FOR_GIT:
            orig_dir = os.getcwd()
            try:
                os.chdir(self.repo.git_dir)
                pto = patch.fromfile(patch_path)
                if pto and pto.apply(strip=0):
                    logger.info(f'Finished patching rev: {rev}')
                    return True
            finally:
                os.chdir(orig_dir)
        else:
            patch_result = self.repo.git.apply(patch_path, "-p1", "--ignore-whitespace", "-v")
            logger.info(f'Finished patching rev: {rev}, result = {patch_result}')

            if src and src.type == "Svn":
                self.retrieve_binaries(binary_files, rev, src)

            if not self.verify_apply(rev, src, diff, files):
                return False

            if self.has_changes(rev, files):
                return True

        logger.info(f"Could not apply patch for rev: {rev}")

    def retrieve_binaries(self, binary_files, rev: str, src: TrackerBase):
        for file in binary_files:
            file_byte_array = src.get_file(rev, file, is_binary=True)
            file_utils.overwrite_file(f"{self.repo_path}/{file}", file_byte_array)

    def format_and_save(self, rev, diff):
        diff_lines = git_format_diff(diff, revision="HEAD")
        patch_path = f"{patches_dir}{self.name}/{rev}.txt"
        with open(patch_path, "w", encoding="utf-8-sig") as patch_file:
            patch_file.write(u"\n".join(diff_lines))
            patch_file.flush()
            patch_file.close()

        return patch_path, u"\n".join(diff_lines)

    def get_file(self, rev, file, is_binary=False, encoding="utf-8-sig"):
        logger.info(f"Pulling contents of file (rev={rev}) = {file} and is_binary={is_binary}")
        if is_binary:
            file_contents = self.run_command("git", ["show", "--binary", f"{rev}:{file}"], return_binary=True)
            return bytearray(file_contents, encoding=encoding)
        else:
            file_contents = self.run_command("git", ["show", f"{rev}:{file}"])
            return "\n".join(file_contents.splitlines(keepends=False))

    def has_changes(self, rev: str, files: list = ()):
        if DUMMY_GIT:
            return True
        response = self.run_command("git", ["ls-files", "-o", "--directory", "--exclude-standard"])
        untracked_files = response.strip().splitlines(keepends=False) if response else []
        return self.repo.is_dirty() or (untracked_files and len(untracked_files) > 0)

    def revert_all(self):
        logger.info("Performing 'git reset --HARD'")
        if DUMMY_GIT or self.is_test:
            return

        self.repo.git.reset("--hard")

    def cleanup(self):
        with self._lock:
            logger.info("Performing 'git cleanup'")
            if DUMMY_GIT or self.is_test:
                return

            lock_file_path = f"{self.repo.git_dir}\\index.lock"
            if os.path.exists(lock_file_path):
                os.remove(lock_file_path)
            else:
                print("No lock file found")

            self.revert_all()
            self.repo.git.clean("-f", "-d")
