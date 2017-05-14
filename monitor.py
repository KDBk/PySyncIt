import argparse
import logging
import os
import sys

from node import Node
from server import Server
from client import Client
import config as sync_config


__author__ = 'dushyant'
__updater__ = 'daidv'


logger = logging.getLogger('syncIt')
USERNAME = sync_config.get('syncit.auth', 'username')
PASSWD = sync_config.get('syncit.auth', 'passwd')



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
        '-ip', help='Specify the ip address of this machine', required=False)

    parser.add_argument(
        '-port', help='Specify the port of this machine to run rpc server', required=False)

    parser.add_argument(
        '-uname', help='Specify the user name of this machine', required=False)
    
    parser.add_argument(
        '-role', help='Specify the role of this machine - client or server', required=False)
    
    args = parser.parse_args()

    #start logging
    setup_logging("syncit.log.%s-%s" % (args.ip, args.port));

    if (args.role == 'server'):
        node = Server(args.role, *sync_config.get_server_tuple(), USERNAME, PASSWD, sync_config.get_watch_dirs(), sync_config.get_clients())
    else:
        node = Client(args.role, *sync_config.get_clients(), USERNAME, PASSWD, sync_config.get_watch_dirs(), sync_config.get_server_tuple())

    node.activate()


if __name__ == "__main__":
    try:
        main()
        while True:
            continue
    except KeyboardInterrupt:
        sys.exit(0)
