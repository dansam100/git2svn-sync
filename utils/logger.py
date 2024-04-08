import errno
import logging
import os

from logging.handlers import TimedRotatingFileHandler

logs_dir = "output/logs/"
log_format_full = '%(asctime)s\t%(name)s\t%(levelname)s\t%(message)s'
log_format_message_only = '%(message)s'


def setup_logger(project_name, location: str = "output/logs"):
    """
    Initialize logging for a given project. Will remove other loggers and set up console and file handlers.
    The log file will rotate anytime you start up the application or after midnight

    :param project_name: The name of the log file (default location is "output/logs/<project_name>.log")
    :param location: the relative/absolute folder location of the log file relative to the application root
    :return: None
    """
    print("Creating logs directory")
    if not os.path.exists(os.path.dirname(logs_dir)):
        try:
            os.makedirs(os.path.dirname(logs_dir))
        except OSError as exc:  # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise

    c_handler = logging.StreamHandler()
    f_handler = NewRotatingFileHandler(f'{location}/{project_name}.log',
                                       backupCount=10,
                                       encoding="utf-8",
                                       when='midnight')
    f_format = logging.Formatter(log_format_full)
    c_handler.setFormatter(f_format)
    f_handler.setFormatter(f_format)

    logging.basicConfig()
    if logging.root.hasHandlers():
        for handler in logging.root.handlers:
            logging.root.removeHandler(handler)

    logging.root.setLevel(logging.INFO)
    logging.root.addHandler(c_handler)
    logging.root.addHandler(f_handler)


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


def get_logger(name):
    logger = logging.getLogger(name)

    return logger


def get_extra_file_logger(name, file_name, log_format: str = log_format_full):
    logger = get_logger(name)
    f_handler = logging.FileHandler(f'output/logs/{file_name}', encoding="utf-8", mode='a')
    f_format = logging.Formatter(log_format)
    f_handler.setFormatter(f_format)
    logger.addHandler(f_handler)

    return logger


def log_to_file(file_name: str, content: str):
    with open(f'output/logs/{file_name}', mode='w', encoding="utf-8") as f:
        f.write(content)


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

