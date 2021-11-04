import os
import subprocess

import collections
import patch
import svn.local
import pprint
import time

from diff_tools import svn_format_diff
from config import svn_url, SWITCH_USER_FOR_COMMITS, DUMMY_SVN, TRACE_LOGS
from config import patches_dir, USE_SVN_PATCH_FORMAT, USE_PATCH_TOOL

repo = svn.local.LocalClient(svn_url)


def run_command(subcommand, args, **kwargs):
    orig_dir = os.getcwd()
    try:
        os.chdir(repo.path)
        cmd = [subcommand] + args
        return subprocess.run(cmd, stdout=subprocess.PIPE).stdout.decode('utf-8')
    finally:
        os.chdir(orig_dir)


print("SVN version:", run_command("svn", ['--version', '--quiet']), "\n")


def run_svn_command(subcommand, args, **kwargs):
    orig_dir = os.getcwd()
    try:
        os.chdir(repo.path)
        return repo.run_command(subcommand, args, **kwargs)
    finally:
        os.chdir(orig_dir)

    return None


def get_last_commit(with_pull=True):
    print("Getting last commit info from svn (svn info)")
    if DUMMY_SVN:
        c = collections.namedtuple('LogEntry', ['date', 'msg', 'revision', 'author', 'changelist'])
        return c(**{'date': time.time(), 'revision': -1, 'msg': "Dummy message", 'author': 'fake_author', 'changedlist': []})

    if with_pull:
        repo.update()

    return list(repo.log_default(limit=1)).pop()


def get_last_commit_info(with_pull=True):
    print("Getting last commit info from svn (svn info)")
    if DUMMY_SVN:
        return

    if with_pull:
        repo.update()

    info = repo.info()

    if TRACE_LOGS:
        pprint.pprint(info)

    return info


def switch_user(user):
    print(f"Performing 'svn relocate {user}'")
    if not SWITCH_USER_FOR_COMMITS or DUMMY_SVN:
        return

    print(f"Switching to user: {user}")
    run_svn_command(f"relocate svn+ssh//{user}@svn_remote_url")


def commit(message, author, rev, diff, files):
    if DUMMY_SVN:
        return "dummy_commit", -1

    switch_user(author)

    commit_msg = f"{message}\n\nSynced from: {rev}"
    if apply(rev, diff):
        print(f"Performing 'svn commit --username {author} -m {message} <diff> {','.join(files)}'")
        repo.commit(commit_msg, files)
        commit_info = get_last_commit(with_pull=True)
        return commit_msg, commit_info.revision
    else:
        return None, None


def apply(rev, diff):
    print(f"Performing 'svn patch <diff>' for rev: {rev}")
    if DUMMY_SVN:
        return

    diff_lines = svn_format_diff(diff, revision=rev) if USE_SVN_PATCH_FORMAT else diff.split("\r\n")
    patch_path = f"{patches_dir}{rev}.txt"
    with open(patch_path, "w", encoding="utf-8", newline="\n") as patch_file:
        patch_file.write("\n".join(diff_lines))
        patch_file.flush()
        patch_file.close()

    if USE_PATCH_TOOL:
        orig_dir = os.getcwd()
        try:
            os.chdir(repo.path)
            pto = patch.fromfile(patch_path)
            print(f'Finished patching rev: {rev}')
            if pto.apply():
                return True
        finally:
            os.chdir(orig_dir)
    else:
        patch_result = run_svn_command("patch", [patch_path])
        print(f'Finished patching rev: {rev}, result = {patch_result}')

        return True if has_changes() else False

    print(f"Could not apply patch for rev: {rev}")


def has_changes():
    status = repo.status()
    if len(list(status)) == 0:
        return False

    return True


def cleanup():
    print("Performing 'svn cleanup'")
    if DUMMY_SVN:
        return

    repo.cleanup()
