"""
log.py

Logging utilities for server program
"""

import logging
from logging.handlers import TimedRotatingFileHandler
import os.path

logger = None

def init_log(fname):
    global logger
    
    print fname
    
    fpath = os.path.dirname(fname)
    if not os.path.exists(fpath):
        os.makedirs(fpath)
    handler = TimedRotatingFileHandler(fname, when='midnight')
    logger = logging.getLogger('cwlint-log')
    logger.setLevel(logging.ERROR)
    logger.addHandler(handler)

def log_message(msg):
    logger.error(msg)
    print msg
    for h in logger.handlers:
        h.flush()