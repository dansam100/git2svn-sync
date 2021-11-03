import sys
import traceback
from time import sleep

import git_tracker as git
import svn_tracker as svn
import tracker


def start_git_revision_tracker():
    print("Starting revision tracker...")
    iteration_count = 0
    commit_count = 0
    while True:
        try:
            last_tracked_rev = tracker.get_last_git_revision()
            git_last_commit = git.get_last_commit(with_pull=False)
            svn_last_commit = {'message': "test", 'commit_revision': 1}  # svn.get_last_commit()
            pending_revs = list(git.get_revisions_since(last_tracked_rev))

            print(f"\n\nIteration: {iteration_count}, {commit_count} commits completed")
            print(f"Last revision (Git): {git_last_commit.message}")
            print(f"Last revision (Svn): {svn_last_commit['commit_revision']}")
            print(f"Revision tracker: last(git) = {git_last_commit}, last(svn) = {svn_last_commit}, pending = {len(pending_revs)}")

            if len(pending_revs) <= 0:
                print("No pending changes...resume in 60 seconds")
                sleep(60)
                continue

            print(f"Revisions (pending):", ", ".join(pending_revs))

            tracker.save_pending_revisions(pending_revs)

            for rev in pending_revs:
                try:
                    msg, author, diff, files = git.get_diff(rev)
                    svn_msg, svn_rev = svn.commit(msg, author, rev, diff, files)
                    commit_count += 1
                    tracker.set_last_revision(rev, svn_rev)
                    sleep(1)
                except Exception as exc:
                    print(f"{exc} occurred in apply diff loop")
                    traceback.print_exc(file=sys.stdout)
                    svn.cleanup()

            iteration_count += 1
        except Exception as loopEx:
            print(f"{loopEx} occurred. Retrying...")
            traceback.print_exc(file=sys.stdout)

    print("Stopping revision tracker...")


if __name__ == '__main__':
    try:
        start_git_revision_tracker()
    except KeyboardInterrupt:
        print("Stopped!")
        raise
    except Exception as ex:
        print(ex)
        traceback.print_exc(file=sys.stdout)
        sys.exit(1)
