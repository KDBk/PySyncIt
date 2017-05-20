import ConfigParser
import logging

from persistence import PersistentSet


__author__ = 'dushyant'
__updater__ = 'daidv'


logger = logging.getLogger('syncIt')
sync_config = ConfigParser.ConfigParser()
sync_config.read('syncit.cfg')


def get_watch_dirs():
    watch_dirs = []
    for key, value in sync_config.items('syncit.dirs'):
        watch_dirs.append(value.strip())
    logger.debug("watched dirs %s", watch_dirs)
    return watch_dirs


def get_node():
    words = sync_config.get('syncit.node', 'node')
    username, port = words.split(',')
    return (username, port)


def get_servers():
    servers = []
    for key, value in sync_config.items('syncit.servers'):
        words = value.split(',')
        passwd, ip, port = [word.strip() for word in words]
        servers.append((passwd, ip, port))
    return servers


__all__ = [get_watch_dirs, get_servers, get_node]
