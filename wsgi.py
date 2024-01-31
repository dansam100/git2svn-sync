import sys
import traceback

import app
import logger

if __name__ == "__main__":
    try:
        app.run_trackers()
        # launch dev webserver
        app.run_web_server()

    except KeyboardInterrupt:
        logger.info("Stopped!")
        raise
    except Exception as ex:
        logger.info(ex)
        traceback.print_exc(file=sys.stdout)
        sys.exit(1)
