import sys
import traceback
import threading
from time import sleep

import config
from utils import tracker, utils
import setup
import web

from utils.logger import get_logger
from repo.tracker_base import TrackerBase

logger = get_logger(__name__)
threads = []


def start_revision_tracker(name: str, source: TrackerBase, target: TrackerBase):
    logger.info(f"Starting revision tracker ({name})...")
    iteration_count = 0
    commit_count = 0
    empty_count = 0
    identical_count = 0

    source.cleanup()
    target.cleanup()
    tracker.initialize(name)

    while True:
        try:
            if config.USE_TRIGGERS_TO_INITIATE_SYNC:
                logger.info(f"{name}: Waiting for trigger to initiate sync")
                utils.wait_until(web.has_trigger_for(name))
                # clear trigger counters
                web.clear_trigger_counter(name)

            pending_revs = tracker.get_pending_revisions(name)
            last_src_tracked_rev, last_tgt_tracked_rev, last_src_tracked_rev_pos = tracker.get_last_revision(name)

            source_last_commit = source.get_last_commit(with_pull=True)
            target_last_commit = target.get_last_commit()

            # reload pending revs if cannot be found
            if len(pending_revs) == 0 or last_src_tracked_rev_pos < 0:
                last_src_tracked_rev_pos = 0
                pending_revs = list(source.get_revisions_since(last_src_tracked_rev))

            source_commit_message = source_last_commit.message.replace('\n', '\t')
            target_commit_message = target_last_commit.message.replace('\n', '\t')

            logger.info(f"{name}: Iteration: {iteration_count}, {commit_count} commits completed, "
                        f"{identical_count} identical, {empty_count} empty commits")

            logger.info(f"{name}: Last source revision: {source_commit_message}")
            logger.info(f"{name}: Last target revision: {target_commit_message}")
            logger.info(f"{name}: Revision sync tracker: last({source.type}) = {source_last_commit.revision}, "
                        f"last({target.type}) = {target_last_commit.revision}, "
                        f"pending = {len(pending_revs)} commits, position = {last_src_tracked_rev_pos}")

            if len(pending_revs) <= 0:
                logger.info(f"{name}: No pending changes...resume in 60 seconds")
                web.clear_trigger_counter(name)
                sleep(60)
                continue

            logger.info(f"{name}: Revisions (pending): {', '.join(map(str, pending_revs))}")

            tracker.save_pending_revisions(name, pending_revs)

            latest_synced_tgt_rev = None
            latest_synced_src_rev = None
            for rev in pending_revs[last_src_tracked_rev_pos:]:
                try:
                    logger.info(f"Processing rev: {rev} from position: {last_src_tracked_rev_pos}")
                    date, msg, author, diff, files = source.get_diff(rev)
                    if not utils.remove_control_characters(str(diff)).strip():
                        logger.info(f"{name}: Diff was empty for revision: {rev}")
                        empty_count += 1
                        continue

                    target_msg, latest_synced_tgt_rev = target.commit(date, msg, author, rev, diff, files, src=source)
                    iteration_count += 1

                    if latest_synced_tgt_rev:
                        commit_count += 1
                        last_src_tracked_rev_pos += 1
                        latest_synced_src_rev = rev
                        # Only update position but keep original start and end points
                        tracker.set_last_revision(name, last_src_tracked_rev, last_tgt_tracked_rev,
                                                  last_src_tracked_rev_pos)
                        sleep(1)
                    else:
                        raise Exception("Patch application produces no revision changes")
                except Exception as exc:
                    logger.error(f"{name}: {exc} occurred in apply diff loop")
                    traceback.print_exc(file=sys.stdout)
                    raise

            # done current batch scenario, move latest revision for src and tgt to final items
            if last_src_tracked_rev_pos >= len(pending_revs):
                logger.info(f"Finished batch of {len(pending_revs)} revisions from index {last_src_tracked_rev_pos}")
                logger.info(f"Saving limit from '{last_src_tracked_rev}' to '{latest_synced_src_rev}'")
                tracker.set_last_revision(name, latest_synced_src_rev, latest_synced_tgt_rev, -1)

        except Exception as loopEx:
            logger.critical(f"{name}: {loopEx} occurred. Cleaning up...")
            traceback.print_exc(file=sys.stdout)

            # clean up
            source.cleanup()
            target.cleanup()

            logger.critical(f"{name}: Cleaned up error. Retrying...")
            logger.critical(f"{name}: Encountered error...resume in 60 seconds")
            sleep(60)

    logger.info(f"Stopping revision tracker ({name}...")


def create_thread(args):
    return threading.Thread(target=start_revision_tracker, args=args, daemon=True)


if __name__ == '__main__':
    try:
        setup.run()

        # initialize trackers
        trackers = setup.get_trackers()
        for trk in trackers:
            web.initialize(trk.name)
            threads.append(create_thread([trk.name, trk.src, trk.tgt]))

        # start all worker threads
        for t in threads:
            t.start()

        # launch dev webserver
        web.run()

    except KeyboardInterrupt:
        logger.info("Stopped!")
        raise
    except Exception as ex:
        logger.info(ex)
        traceback.print_exc(file=sys.stdout)
        sys.exit(1)
