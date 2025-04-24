import logging
def get_logger(name):
    logger = logging.getLogger('erdapy')
    logger.setLevel(logging.INFO)
    return logger
