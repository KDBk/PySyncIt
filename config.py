import ConfigParser
import logging

from persistence import PersistentSet


__author__ = 'dushyant'
__updater__ = 'daidv'


logger = logging.getLogger('syncIt')
sync_config = ConfigParser.ConfigParser()
sync_config.read('syncit.cfg')


class ClientData(object):
    """Data corresponding to each client residing in server object"""
    def __init__(self, client_key, client_ip, client_port):
        self.available = False
        self.mfiles = PersistentSet('server-%s.pkl'%(client_key))
        self.ip = client_ip
        self.port = client_port


def get_watch_dirs():
    watch_dirs = []
    for key, value in sync_config.items('syncit.dirs'):
        watch_dirs.append(value.strip())
    logger.debug("watched dirs %s", watch_dirs)
    return watch_dirs


def get_clients():
    clients = []
    for key, value in sync_config.items('syncit.clients'):
        words = value.split(',')
        client_ip, client_port = [word.strip() for word in words]
        clients.append(ClientData(key, client_ip, int(client_port)))
    return clients


def get_server_tuple():
    server_ip, server_port = sync_config.get('syncit.server', 'server', 1).split(',')
    return (server_ip, server_port)


def get_auth():
    username = sync_config.get('syncit.auth', 'username')
    passwd = sync_config.get('syncit.auth', 'passwd')
    return (username, passwd)


__all__ = [get_watch_dirs, get_clients, get_server_tuple, get_auth]
