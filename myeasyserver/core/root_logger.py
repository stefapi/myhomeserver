#  Copyright (c) 2024  stefapi
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import logging
import sys
import os
from ..version import __software__

from ..backend.config import config

LOGGER_FILE = os.path.join(config.path.LOG_DIR, __software__+".log")
DATE_FORMAT = "%d-%b-%y %H:%M:%S"
LOGGER_FORMAT = "%(levelname)s: %(asctime)s \t%(message)s"

logging.basicConfig(level=logging.INFO, format=LOGGER_FORMAT, datefmt="%d-%b-%y %H:%M:%S")


def logger_init() -> logging.Logger:
    """
    The logger_init function initializes the logger object.
    It creates a file handler and a stream handler, and adds them to the logger object.
    The file handler logs all messages to LOGGER_FILE, while the stream handler logs all messages to stdout.

    :return: The root logger object
    """

    logger = logging.getLogger(__software__)
    logger.propagate = False

    # File Handler
    output_file_handler = logging.FileHandler(LOGGER_FILE)
    handler_format = logging.Formatter(LOGGER_FORMAT, datefmt=DATE_FORMAT)
    output_file_handler.setFormatter(handler_format)

    # Stdout
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(handler_format)

    logger.addHandler(output_file_handler)
    logger.addHandler(stdout_handler)

    return logger


root_logger = logger_init()


def get_logger(module=None) -> logging.Logger:
    """
    The get_logger function is a helper function that returns a child logger.
    It is used to create loggers for each module in the package, and can be called with no arguments
    to return the root logger.  If given an argument, it will return a child of that logger based on the module given.

    :param module=None: Used to Get the root logger.
    :return: A child logger for the application.
    """
    global root_logger

    if module is None:
        return root_logger

    return root_logger.getChild(module)
