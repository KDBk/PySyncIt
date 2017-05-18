import errno
import logging
import os
import re
import time

import config
import rpc
from node import Node

import logging
import os
import platform
import subprocess
import threading
import time

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

import rpc
from node import Node
from persistence import FilesPersistentSet

__author__ = 'dushyant'
__updater__ = 'daidv'

logger = logging.getLogger('syncIt')
PSCP_COMMAND = {'Linux': 'pscp', 'Windows': 'C:\pscp.exe'}
ENV = platform.system()
PIPE = subprocess.PIPE


def is_collision_file(filename):
    backup_file_pattern = re.compile(r"\.backup\.[1-9]+\.")
    if re.search(backup_file_pattern, filename) is None:
        return False
    else:
        return True


class Handler(FileSystemEventHandler):
    def __init__(self, mfiles, rfiles, pulledfiles):
        self.mfiles = mfiles
        self.rfiles = rfiles
        self.pulled_files = pulledfiles

    # @staticmethod
    def on_any_event(self, event):
        if event.is_directory:
            return None

        elif event.event_type == 'created':
            filename = event.src_path
            if not self.pulled_files.__contains__(filename):
                self.mfiles.add(filename, time.time())
                logger.info("Created file: %s", filename)
            else:
                pass
                self.pulled_files.remove(filename)

        elif event.event_type == 'modified':
            filename = event.src_path
            if not self.pulled_files.__contains__(filename):
                self.mfiles.add(filename, time.time())
                logger.info("Modified file: %s", filename)
            else:
                self.pulled_files.remove(filename)

        elif event.event_type == 'deleted':
            filename = event.src_path
            self.rfiles.add(filename)
            try:
                self.mfiles.remove(filename)
            except KeyError:
                pass
            logger.info("Removed file: %s", filename)


class Server(Node):
    """Server class"""

    def __init__(self, ip, port, uname, passwd, watch_dirs, clients, server):
        super(Server, self).__init__(ip, port, uname, passwd, watch_dirs)
        self.clients = clients
        self.server = server
        self.mfiles = FilesPersistentSet(pkl_filename='client.pkl')  # set() #set of modified files
        self.rfiles = set()  # set of removed files
        self.pulled_files = set()
        self.server_available = True

    def push_file(self, filename, dest_file, dest_uname, dest_ip):
        """push file 'filename' to the destination"""
        command = "{} -q -l {} -pw {} {} {}@{}:{}".format(
            PSCP_COMMAND[ENV], self.username, self.passwd,
            filename, dest_uname, dest_ip, dest_file).split()
        print(command)
        proc = subprocess.Popen(command, stdout=PIPE, stderr=PIPE, stdin=PIPE)
        proc.stdin.write('y')
        push_status = proc.wait()
        logger.debug("returned status %s", push_status)
        return push_status

    def pull_file(self, filename, source_file, source_uname, source_ip):
        """pull file 'filename' from the source"""
        my_file = "{}{}".format(self.watch_dirs[0], filename)
        self.pulled_files.add(my_file)
        command = "{} -qp -l {} -pw {} {}@{}:{} {}".format(
            PSCP_COMMAND[ENV], self.username, self.passwd, source_uname,
            source_ip, source_file, my_file).split()
        print(command)
        proc = subprocess.Popen(command, stdout=PIPE, stderr=PIPE, stdin=PIPE)
        proc.stdin.write('y')
        return_status = proc.wait()
        logger.debug("returned status %s", return_status)

    def req_push_file(self, filename):
        """Mark this file as to be notified to clients - this file 'filename' has been modified, pull the latest copy"""
        logger.debug("server filedata %s", filename)
        my_file = "{}{}".format(self.watch_dirs[0], filename)
        server_filename = my_file

        logger.debug("server filename %s returned for file %s", server_filename, filename)
        return (self.username, server_filename)

    def ack_push_file(self, server_filename, source_uname, source_ip, source_port):
        """Mark this file as to be notified to clients - this file 'filename' has been modified, pull the latest copy"""
        if is_collision_file(server_filename):
            return

        for client in self.clients:
            logger.debug("tuple %s : %s", (client.ip, client.port), (source_ip, source_port))
            if (client.ip, client.port) == (source_ip, source_port):
                continue
            else:
                # client.mfiles.add(server_filename)
                logger.debug("add file to modified list")

    def check_collision(self, filedata):
        # As a temporary, we are not using it.
        # This is so dangerous if two client push same file in the same time
        my_file = self.get_dest_path(filedata['name'])
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

    def sync_files_to_clients(self):
        """Actual call to clients to pull files"""
        while True:
            try:
                time.sleep(10)
                for client in self.clients:
                    logger.debug("list of files for client %s, availability %s", client.mfiles.list(), client.available)
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

    def sync_files_to_server(self):
        """Sync all the files present in the mfiles set and push this set"""
        mfiles = self.mfiles
        while True:
            try:
                time.sleep(10)
                for filedata in mfiles.list():
                    filename = filedata.name
                    if not filename or '.swp' in filename:
                        continue
                    logger.info("push filedata object to server %s", filedata)
                    server_ip, server_port = self.server
                    # Add by daidv, only send file name alter for full path file to server
                    filedata_name = self.format_file_name(filedata.name)
                    server_uname, dest_file = rpc.req_push_file(server_ip, server_port, filedata_name)
                    logger.debug("destination file name %s", dest_file)
                    if dest_file is None:
                        break
                    push_status = self.push_file(filename, dest_file, server_uname, server_ip)
                    if (push_status < 0):
                        break
                    rpc_status = rpc.ack_push_file(server_ip, server_port, dest_file, self.username, self.ip, self.port)

                    if rpc_status is None:
                        break
                    mfiles.remove(filename)
                self.mfiles.update_modified_timestamp()
            except KeyboardInterrupt:
                break

    def mark_presence_from_client(self):
        """Mark client as available"""
        server_ip, server_port = self.server
        rpc.mark_presence(server_ip, server_port, self.ip, self.port)

    def mark_presence_as_server(self, client_ip, client_port):
        """Mark client as available"""
        for client in self.clients:
            if (client_ip, client_port) == (client.ip, client.port):
                client.available = True

    def find_modified(self):
        """Find all those files which have been modified when sync demon was not running"""
        for directory in self.watch_dirs:
            dirwalk = os.walk(directory)

            for tuple in dirwalk:
                dirname, dirnames, filenames = tuple
                break

            for filename in filenames:
                file_path = os.path.join(dirname, filename)
                logger.debug("checked file if modified before client was running: %s", file_path)
                mtime = os.path.getmtime(file_path)
                # TODO save and restore last_synctime
                if mtime > self.mfiles.get_modified_timestamp():
                    logger.debug("modified before client was running %s", file_path)
                    self.mfiles.add(file_path, mtime)

    def find_available_clients(self):
        for client in self.clients:
            client.available = rpc.find_available(client.ip, client.port)
            logger.debug("client marked available")

    def watch_files(self):
        """keep a watch on files present in sync directories"""
        ob = Observer()
        # watched events
        ob.schedule(Handler(self.mfiles, self.rfiles, self.pulled_files), self.watch_dirs[0])
        ob.start()
        logger.debug("watched dir %s", self.watch_dirs)
        try:
            while True:
                time.sleep(5)
        except:
            self.ob.stop()
            print "Error"

    def start_watch_thread(self):
        """Start threads to find modified files """
        watch_thread = threading.Thread(target=self.watch_files)
        watch_thread.setDaemon(True)
        watch_thread.start()
        logger.info("Thread 'watchfiles' started ")

    def activate(self):
        """ Activate Server Node """
        super(Server, self).activate()
        self.find_available_clients()
        self.start_watch_thread()
        self.mark_presence_from_client()
        self.find_modified()
