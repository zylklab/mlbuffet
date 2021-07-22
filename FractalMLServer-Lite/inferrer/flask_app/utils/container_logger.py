import logging
import sys
import time
from logging.handlers import TimedRotatingFileHandler


class Logger():

    def __init__(self, filename):
        self.FORMATTER = logging.Formatter("%(asctime)s — %(name)s — %(levelname)s — %(message)s")
        self.LOG_FILE = f'/home/logs/{filename}-{time.time()}.log'

        """DEBUG"""
        # self.LOG_FILE = f'/tmp/{filename}-{time.time()}.log'

        # TODO
        # self.LOG_LEVEL = DEBUG
        # esto debería ir a un properties

    def get_console_handler(self):
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(self.FORMATTER)
        return console_handler

    def get_file_handler(self):
        file_handler = TimedRotatingFileHandler(self.LOG_FILE, when='midnight')
        file_handler.setFormatter(self.FORMATTER)
        return file_handler

    def get_logger(self, logger_name):
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG)  # better to have too much log than not enough
        logger.addHandler(self.get_console_handler())
        logger.addHandler(self.get_file_handler())
        # with this pattern, it's rarely necessary to propagate the error up to parent
        logger.propagate = False
        return logger
