import errno
import logging
import os
from datetime import date, timedelta

from logging.handlers import TimedRotatingFileHandler

logs_dir = "./logs/"
print("Creating logs directory")
if not os.path.exists(os.path.dirname(logs_dir)):
    try:
        os.makedirs(os.path.dirname(logs_dir))
    except OSError as exc:  # Guard against race condition
        if exc.errno != errno.EEXIST:
            raise


class NewRotatingFileHandler(TimedRotatingFileHandler):

    def __init__(self, *args, **kws):
        if kws.__contains__('compress_mode'):
            compress_mode = kws.pop('compress_mode')
            try:
                self.compress_cls = COMPRESSION_SUPPORTED[compress_mode]
            except KeyError:
                raise ValueError('"%s" compression method not supported.' % compress_mode)

        super(NewRotatingFileHandler, self).__init__(*args, **kws)

    def doRollover(self):
        super(NewRotatingFileHandler, self).doRollover()

        # # Compress the old log.
        # yesterday = date.today() - timedelta(days=1)
        # old_log = self.baseFilename + yesterday.strftime("%Y-%m-%d")
        # with open(old_log) as log:
        #     with self.compress_cls.open(old_log + '.gz', 'wb') as comp_log:
        #         comp_log.writelines(log)
        #
        # os.remove(old_log)


# Settings
c_handler = logging.StreamHandler()
f_handler = NewRotatingFileHandler('logs/git2svn-sync.log', backupCount=10, encoding="utf-8", when='midnight')
f_format = logging.Formatter('%(asctime)s\t%(name)s\t%(levelname)s\t%(message)s')
c_handler.setFormatter(f_format)
f_handler.setFormatter(f_format)

logging.basicConfig()
if logging.root.hasHandlers():
    for handler in logging.root.handlers:
        logging.root.removeHandler(handler)

logging.root.setLevel(logging.INFO)
logging.root.addHandler(c_handler)
logging.root.addHandler(f_handler)


def get_logger(name):
    logger = logging.getLogger(name)

    return logger


COMPRESSION_SUPPORTED = {}

try:
    import gzip

    COMPRESSION_SUPPORTED['gz'] = gzip
except ImportError:
    pass

try:
    import zipfile

    COMPRESSION_SUPPORTED['zip'] = zipfile
except ImportError:
    pass

