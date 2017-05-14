import logging
import re
import threading
import time
import errno
from node import Node
from persistence import PersistentSet
import subprocess
import os

import rpc
import config as sync_config

__author__ = 'dushyant'
__updater__ = 'daidv'

logger = logging.getLogger('syncIt')
USERNAME = sync_config.get('syncit.auth', 'username')
PASSWD = sync_config.get('syncit.auth', 'passwd')


def is_collision_file(filename):
    backup_file_pattern = re.compile(r"\.backup\.[1-9]+\.")
    if re.search(backup_file_pattern, filename) is None:
        return False
    else:
        return True


class ClientData(object):
    """Data corresponding to each client residing in server object"""
    def __init__(self, client_uname, client_ip, client_port):
        self.available = False
        self.mfiles = PersistentSet('server-%s.pkl'%(client_uname))
        self.uname = client_uname
        self.ip = client_ip
        self.port = client_port

class Server(Node):
    """Server class"""
    def __init__(self, role, ip, port, uname, passwd, watch_dirs, clients):
        super(Server, self).__init__(role, ip, port, uname, passwd, watch_dirs)
        self.clients = clients

    def req_push_file(self, filename):
        """Mark this file as to be notified to clients - this file 'filename' has been modified, pull the latest copy"""
        logger.debug("server filedata %s", filename)
        my_file = "{}{}".format(self.watch_dirs[0], filename)
        server_filename = my_file

        logger.debug("server filename %s returned for file %s", server_filename, filename)
        return (USERNAME, server_filename)

    def ack_push_file(self, server_filename, source_uname, source_ip, source_port):
        """Mark this file as to be notified to clients - this file 'filename' has been modified, pull the latest copy"""
        if is_collision_file(server_filename):
            return

        for client in self.clients:
            logger.debug("tuple %s : %s",(client.ip, client.port), (source_ip, source_port))
            if (client.ip, client.port) == (source_ip, source_port):
                continue
            else:
                client.mfiles.add(server_filename)
                logger.debug("add file to modified list")

    def check_collision(self, filedata):
        # As a temporary, we are not using it.
        # This is so dangerous if two client push same file in the same time
        my_file = Node.get_dest_path(filedata['name'], self.username)
        try:
           collision_exist = os.path.getmtime(my_file) > filedata['time']
           logger.debug("collision check: server time %s  client time %s", os.path.getmtime(my_file), filedata['time'])
        except OSError as e:
            if e.errno == errno.ENOENT:
                collision_exist = False
            else:
                raise
        logger.debug("collision check for file %s result %s", my_file, collision_exist)
        return collision_exist

    def sync_files(self):
        """Actual call to clients to pull files"""
        while True:
            try:
                time.sleep(10)
                for client in self.clients:
                    logger.debug( "list of files for client %s, availability %s",client.mfiles.list(), client.available)
                    if client.available:
                        for file in client.mfiles.list():
                            onlye_file_name = self.format_file_name(file)
                            rpc_status = rpc.pull_file(client.ip, client.port, onlye_file_name, file, self.username, self.ip)

                            if rpc_status is None:
                                client.available = False
                                continue
                            client.mfiles.remove(file)
                            logger.debug("actual sync")
            except KeyboardInterrupt:
                break


    def mark_presence(self, client_ip, client_port):
        """Mark client as available"""
        logger.debug("mark available call received")
        for client in self.clients:
            if (client_ip, client_port) == (client.ip, client.port):
                client.available = True
                logger.debug("client with ip %s, marked available", client_ip)

    def find_available_clients(self):
        for client in self.clients:
            client.available = rpc.find_available(client.ip, client.port)
            logger.debug("client marked available")

    def activate(self):
        """ Activate Server Node """
        super(Server, self).activate()
        self.find_available_clients()

