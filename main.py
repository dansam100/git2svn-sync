import sys
import traceback

from server import app
from utils.logger import setup_logger, get_logger

setup_logger('git2svn-sync')

logger = get_logger(__name__)

if __name__ == "__main__":
    try:
        app.run()
    except KeyboardInterrupt:
        logger.info("Stopped!")
        raise
    except Exception as ex:
        logger.info(ex)
        traceback.print_exc(file=sys.stdout)
        sys.exit(1)
