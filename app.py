import os
import errno

import sys
import traceback
from time import sleep

import unicodedata

from config import patches_dir
import git_tracker as git
import svn_tracker as svn
import tracker


def start_git_revision_tracker():
    print("Starting revision tracker...")
    iteration_count = 0
    commit_count = 0
    empty_count = 0

    svn.cleanup()

    while True:
        try:
            last_tracked_rev = tracker.get_last_git_revision()
            git_last_commit = git.get_last_commit(with_pull=True)
            svn_last_commit = svn.get_last_commit()
            pending_revs = list(git.get_revisions_since(last_tracked_rev))

            git_commit_message = git_last_commit.message.replace('\n', '\t')
            svn_commit_message = svn_last_commit.msg.replace('\n', '\t')

            print(f"\n\nIteration: {iteration_count}, {commit_count} commits completed")
            print(f"Last revision (Git): {git_commit_message}")
            print(f"Last revision (Svn): {svn_commit_message}")
            print(f"Revision tracker: last(git) = {git_last_commit.hexsha}, last(svn) = {svn_last_commit.revision}, "
                  f"pending = {len(pending_revs)} commits")

            if len(pending_revs) <= 0:
                print("No pending changes...resume in 60 seconds")
                sleep(60)
                continue

            print(f"Revisions (pending): ", ", ".join(pending_revs))

            tracker.save_pending_revisions(pending_revs)

            for rev in pending_revs:
                try:
                    msg, author, diff, files = git.get_diff(rev)
                    if not remove_control_characters(str(diff)).strip():
                        empty_count += 1
                        continue

                    svn_msg, svn_rev = svn.commit(msg, author, rev, diff, files)
                    if svn_rev:
                        commit_count += 1
                        tracker.set_last_revision(rev, svn_rev)

                    sleep(1)
                except Exception as exc:
                    print(f"{exc} occurred in apply diff loop")
                    traceback.print_exc(file=sys.stdout)
                    svn.cleanup()

            iteration_count += 1
        except Exception as loopEx:
            svn.cleanup()
            print(f"{loopEx} occurred. Retrying...")
            traceback.print_exc(file=sys.stdout)

    print("Stopping revision tracker...")


def remove_control_characters(s):
    result = ""
    for ch in s:
        if unicodedata.category(ch)[0] != "C":
            result += ch
        else:
            result += ';'

    return result


def setup():
    if not os.path.exists(os.path.dirname(patches_dir)):
        try:
            os.makedirs(os.path.dirname(patches_dir))
        except OSError as exc:  # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise


if __name__ == '__main__':
    try:
        setup()
        start_git_revision_tracker()
    except KeyboardInterrupt:
        print("Stopped!")
        raise
    except Exception as ex:
        print(ex)
        traceback.print_exc(file=sys.stdout)
        sys.exit(1)
