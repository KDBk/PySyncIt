import argparse
import logging
import os
import sys

from node import Node
from server import Server
from client import Client
import config


__author__ = 'dushyant'
__updater__ = 'daidv'


logger = logging.getLogger('syncIt')
USERNAME = config.sync_config.get('syncit.auth', 'username')
PASSWD = config.sync_config.get('syncit.auth', 'passwd')



def setup_logging(log_filename):
    handler = logging.FileHandler(log_filename)
#    handler = logging.StreamHandler()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    print 'Logging started on file %s' % log_filename


def main():
    #use argparse to get role, ip, port and user name
    parser = argparse.ArgumentParser(
        description="""PySyncIt""",
        formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument(
        '-role', help='Specify the role of this machine - client or server', required=False)
    
    args = parser.parse_args()

    #start logging
    server = config.get_server_tuple()
    clients = config.get_clients()
    watch_dirs = config.get_watch_dirs()

    if (args.role == 'server'):
        node = Server(args.role, server[0], server[1], USERNAME, PASSWD, watch_dirs, clients)
        setup_logging("syncit.log.%s-%s" % (server[0], server[1]))
    else:
        node = Client(args.role, clients[0].ip, clients[0].port, USERNAME, PASSWD, watch_dirs, server)
        setup_logging("syncit.log.%s-%s" % (clients[0].ip, clients[0].port))

    node.activate()


if __name__ == "__main__":
    try:
        main()
        while True:
            continue
    except KeyboardInterrupt:
        sys.exit(0)
