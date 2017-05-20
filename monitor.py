import sys
import logging
import config
from server import Server

__author__ = 'dushyant'
__updater__ = 'daidv'


logger = logging.getLogger('syncIt')


def setup_logging(log_filename):
    handler = logging.FileHandler(log_filename)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    print 'Logging started on file %s' % log_filename


if __name__ == "__main__":
    try:
        # start logging
        servers = config.get_servers()
        watch_dirs = config.get_watch_dirs()
        this = config.get_node()
        node = Server(this[0], this[1], watch_dirs, servers)
        setup_logging("syncit.log.%s-%s" % (this[0], this[1]))
        node.activate()
        while True:
            continue
    except KeyboardInterrupt:
        sys.exit(0)
