import argparse
import logging
import os
import sys

from node import Node
from server import Server, ClientData
from client import Client
import config as sync_config


__author__ = 'dushyant'
__updater__ = 'daidv'


logger = logging.getLogger('syncIt')


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
        '-ip', help='Specify the ip address of this machine', required=True)

    parser.add_argument(
        '-port', help='Specify the port of this machine to run rpc server', required=True)

    parser.add_argument(
        '-uname', help='Specify the user name of this machine', required=True)
    
    parser.add_argument(
        '-role', help='Specify the role of this machine - client or server', required=True)
    
    args = parser.parse_args()

    #start logging
    setup_logging("syncit.log.%s-%s" % (args.ip, args.port));

    if (args.role == 'server'):
        node = Server(args.role, args.ip, int(args.port), args.uname, sync_config.get_watch_dirs(), sync_config.get_clients())
    else:
        node = Client(args.role, args.ip, int(args.port), args.uname, sync_config.get_watch_dirs(), sync_config.get_server_tuple())

    node.activate()


if __name__ == "__main__":
    try:
        main()
        while True:
            continue
    except KeyboardInterrupt:
        sys.exit(0)
