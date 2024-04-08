import os
import subprocess
import logging

import collections
import patch
import svn.local
import pprint
import time

from datetime import timezone
import dateutil.parser as dateparser

from utils import file_utils
from repo.tracker_base import TrackerBase

from utils.diff_tools import svn_format_diff, git_get_binary_files, git_get_rename_files
from server.config import DUMMY_SVN
from server.config import patches_dir, USE_SVN_PATCH_FORMAT, USE_PATCH_TOOL_FOR_SVN
from utils.logger import get_logger

logger = get_logger(__name__)


class SvnTracker(TrackerBase):
    def __init__(self, name, url, branch, is_test=False, **kwargs):
        TrackerBase.__init__(self, name, "Svn", url, **kwargs)
        self.branch = branch
        self.is_test = is_test
        self.repo = svn.local.LocalClient(url)

        logger.info("SVN version:" + self.run_command("svn", ['--version', '--quiet']).strip())

    def run_command(self, subcommand, args=(), encoding="utf-8-sig", return_binary=False):
        orig_dir = os.getcwd()
        try:
            args = [] if len(args) == 0 else args
            os.chdir(self.repo.path)
            cmd = [subcommand] + args
            svn_cmd = subprocess.Popen(cmd, stdout=subprocess.PIPE)
            return svn_cmd.communicate()[0].decode(encoding=encoding)
        finally:
            os.chdir(orig_dir)

    def run_svn_command(self, subcommand, args=(), **kwargs):
        args = [] if len(args) == 0 else args
        return self.repo.run_command(subcommand, args, **kwargs, wd=self.repo.path)

    def get_last_commit(self, with_pull=True):
        logger.info("Getting last commit info from svn (svn info)")
        c = collections.namedtuple('LogEntry', ['date', 'message', 'revision', 'author', 'changelist'])
        if DUMMY_SVN:
            return c(**{'date': time.time(), 'revision': -1, 'msg': "Dummy message",
                        'author': 'fake_author', 'changedlist': []})

        if with_pull:
            self.repo.update()

        last_commit = list(self.repo.log_default(limit=1)).pop()
        return c(**{'date': last_commit.date, 'revision': last_commit.revision, 'message': last_commit.msg,
                    'author': last_commit.author, 'changelist': last_commit.changelist})

    def get_last_commit_info(self, with_pull=True):
        logger.info("Getting last commit info from svn (svn info)")
        if DUMMY_SVN:
            return

        if with_pull:
            self.repo.update()

        info = self.repo.info()

        if logger.isEnabledFor(logging.DEBUG):
            pprint.pprint(info)

        return info

    def get_revisions_since(self, rev):
        if DUMMY_SVN:
            return []

        revs = self.repo.log_default(revision_from=f"{rev}")
        revs = list(map(lambda x: x.revision, revs))
        revs.pop(0)

        return revs

    def get_diff(self, rev, is_git_diff=True):
        if DUMMY_SVN:
            return ""

        if not is_git_diff:
            diff = self.run_svn_command("diff", ["-r", f"{int(rev) - 1}:{rev}", "-x", "-U10"])
        else:
            diff = self.run_command("svn", ["diff", "--git", "-r", f"{int(rev) - 1}:{rev}", "-x", "-U10"])

        log = list(self.repo.log_default(revision_from=rev, revision_to=rev)).pop()
        author = log.author
        msg = log.msg
        date = log.date

        if isinstance(diff, list):
            diff = "\n".join(diff)

        files = map(lambda x: x[0], log.changelist) if log.changelist else []
        logger.debug(f"Diff (revision = {rev})\n\n{diff}")
        logger.debug(f"Files (revision = {rev}, count = {len(files)})\n\n{files}")

        return date, msg, author, diff, files

    def commit(self, date, msg, author, rev, diff, files=(), src: TrackerBase = None):
        if DUMMY_SVN or self.is_test:
            return "dummy_commit", -1

        username = author.split('@')[0]
        commit_msg = f"{msg}\n\n#author:{username}\n\n#Synced from: {rev}"
        if self.apply(rev, diff, src, files):
            logger.info(f"Performing 'svn commit --username {username} -m {msg} <diff> {','.join(files)}'")
            self.repo.commit(commit_msg)
            logger.info(f"Commit successful, begin check for updating author to {username}")
            commit_info = self.get_last_commit(with_pull=True)

            # Update commit author
            if username != commit_info.author:
                logger.info(f"Author mismatch: updating author from '{commit_info.author}' to '{username}")
                commit_info = self.update_author(commit_info.revision, username)
            else:
                logger.info(f"Author is already set to {username}")

            # Update commit date: 2022-01-18 21:10:38 -0500
            date_obj = date if type(date) is date else dateparser.parse(date)
            if date_obj != commit_info.date:
                logger.info(f"Commit date mismatch: updating date from '{commit_info.date}' to '{date_obj}")
                commit_info = self.update_timestamp(commit_info.revision, date_obj)
            else:
                logger.info(f"Date is already set to {date}")

            return commit_msg, commit_info.revision
        else:
            return None, None

    def update_author(self, revision, username):
        logger.info(f"Updating author to '{username}' on r{revision}")
        if DUMMY_SVN:
            return self.get_last_commit(with_pull=True)

        svn_rev = revision
        try:
            self.run_svn_command('propset', ['--revprop', f"-r{svn_rev}", 'svn:author', username])
            commit_info = self.get_last_commit(with_pull=True)
            logger.info(f"Successfully updated author to {username} on r{revision}")
            return commit_info
        except Exception as exc:
            logger.info(f"Failed to update author on revision=r{svn_rev} to '{username} due to: {exc}")
            raise exc

    def update_timestamp(self, revision, timestamp):
        logger.info(f"Updating date to '{timestamp}' on r{revision}")
        if DUMMY_SVN:
            return self.get_last_commit(with_pull=True)

        svn_rev = revision
        try:
            time_str = timestamp.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            self.run_svn_command('propset', ['--revprop', f"-r{svn_rev}", 'svn:date', time_str])
            commit_info = self.get_last_commit(with_pull=True)
            logger.info(f"Successfully updated date to {timestamp} on r{revision}")
            return commit_info
        except Exception as exc:
            logger.info(f"Failed to update date on revision=r{svn_rev} to '{timestamp} due to: {exc}")
            raise exc

    def apply(self, rev, diff, src: TrackerBase = None, files: list = ()):
        logger.info(f"Performing 'svn patch <diff>' for rev: {rev}")
        if DUMMY_SVN:
            return

        patch_path, formatted_diff = self.format_and_save(rev, diff)
        binary_files = git_get_binary_files(formatted_diff)
        renamed_files = git_get_rename_files(diff)

        if USE_PATCH_TOOL_FOR_SVN:
            orig_dir = os.getcwd()
            try:
                os.chdir(self.repo.path)
                pto = patch.fromfile(patch_path)
                logger.info(f'Finished patching rev: {rev}')
                if pto.apply():
                    return True
            finally:
                os.chdir(orig_dir)
        else:
            patch_result = self.run_svn_command("patch", [patch_path])
            logger.info(f'Finished patching rev: {rev}, result = {patch_result}')

            if src and src.type == "Git":
                self.retrieve_binaries(binary_files, rev, src)
                self.force_rename(renamed_files)

            if not self.verify_apply(rev, src, diff, files):
                return False

            return True if self.has_changes(rev, files) else False

        logger.info(f"Could not apply patch for rev: {rev}")

    def force_rename(self, renamed_files):
        # handle file renames
        for file in renamed_files:
            to_file = f"{self.repo.path}/{file['to']}"
            from_file = f"{self.repo.path}/{file['from']}"
            logger.info(f"Renaming {from_file} to {to_file}")
            file_utils.create_folders(to_file)
            self.run_svn_command("mv", ["--force", "--parents", from_file, to_file])
        if len(renamed_files) > 0:
            logger.info(self.run_svn_command("stat"))

    def retrieve_binaries(self, binary_files, rev: str, src: TrackerBase):
        """directly retrieve binaries from the revision control system"""
        for file in binary_files:
            ba = bytearray(src.run_command("git", ["show", "--binary", f"{rev}:{file}"], return_binary=True))
            self.overwrite_file(file, ba)

    def format_and_save(self, rev, diff: str):
        diff_lines = svn_format_diff(diff, revision=rev) if USE_SVN_PATCH_FORMAT else diff.splitlines(keepends=False)
        patch_path = f"{patches_dir}{self.name}/{rev}.txt"
        with open(patch_path, "w", encoding="utf-8-sig", newline="\n") as patch_file:
            patch_file.write(u"\n".join(diff_lines))
            patch_file.flush()
            patch_file.close()

        return patch_path, "\n".join(diff_lines)

    def get_file(self, rev, file, is_binary=False, encoding="utf-8-sig"):
        logger.info(f"Pulling contents of file (rev={rev}) = {file} and is_binary={is_binary}")
        file_contents = self.run_command("svn", ["cat", "-r", rev, file])
        if is_binary:
            return bytearray(file_contents, encoding=encoding)

        return "\n".join(file_contents.splitlines(keepends=False))

    def overwrite_file(self, file, contents):
        super().overwrite_file(file, contents)
        self.run_svn_command("add", ["--force", "--parents", file])

    def has_changes(self, rev: str, files: list = ()):
        if DUMMY_SVN:
            return True

        status = self.repo.status()
        if len(list(status)) == 0:
            return False

        return True

    def revert_all(self):
        logger.info("Performing 'svn revert --depth=infinity .'")
        if DUMMY_SVN or self.is_test:
            return

        self.run_svn_command("revert", ['--depth=infinity', '.'])

    def cleanup(self):
        logger.info("Performing 'svn cleanup'")
        if DUMMY_SVN or self.is_test:
            return
        cleanup_args = ["--remove-unversioned", "--remove-ignored"]
        self.run_svn_command('cleanup')
        self.revert_all()
        self.run_svn_command('cleanup', cleanup_args)
