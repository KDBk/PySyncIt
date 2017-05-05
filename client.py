import logging
import rpc
# from pyinotify import WatchManager, ProcessEvent
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
# import pyinotify
import subprocess
import time
import threading
import os
from node import Node
from persistence import FileData, FilesPersistentSet
import shlex

__author__ = 'daidv'

logger = logging.getLogger('syncIt')


class Handler(FileSystemEventHandler):
    def __init__(self, mfiles, rfiles, pulledfiles):
        self.mfiles = mfiles
        self.rfiles = rfiles
        self.pulled_files = pulledfiles

    @staticmethod
    def on_any_event(event):
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


# # Find which files to sync
# class PTmp(ProcessEvent):
#     """Find which files to sync"""
#
#     def __init__(self, mfiles, rfiles, pulledfiles):
#         self.mfiles = mfiles
#         self.rfiles = rfiles
#         self.pulled_files = pulledfiles
#
#     def process_IN_CREATE(self, event):
#         filename = os.path.join(event.path, event.name)
#         if not self.pulled_files.__contains__(filename):
#             self.mfiles.add(filename, time.time())
#             logger.info("Created file: %s", filename)
#         else:
#             pass
#             self.pulled_files.remove(filename)
#
#     def process_IN_DELETE(self, event):
#         filename = os.path.join(event.path, event.name)
#         self.rfiles.add(filename)
#         try:
#             self.mfiles.remove(filename)
#         except KeyError:
#             pass
#         logger.info("Removed file: %s", filename)
#
#     def process_IN_MODIFY(self, event):
#         filename = os.path.join(event.path, event.name)
#         if not self.pulled_files.__contains__(filename):
#             self.mfiles.add(filename, time.time())
#             logger.info("Modified file: %s", filename)
#         else:
#             self.pulled_files.remove(filename)


class Client(Node):
    """Client class"""

    def __init__(self, role, ip, port, uname, watch_dirs, server):
        super(Client, self).__init__(role, ip, port, uname, watch_dirs)
        self.server = server
        self.mfiles = FilesPersistentSet(pkl_filename='client.pkl')  # set() #set of modified files
        self.rfiles = set()  # set of removed files
        self.pulled_files = set()
        self.server_available = True

    def push_file(self, filename, dest_file, dest_uname, dest_ip):
        """push file 'filename' to the destination"""
        # dest_file = Node.get_dest_path(filename, dest_uname)
        command = "echo y | pscp -l daidv -pw 1 {} {}@{}:{}".format(
            filename, dest_uname, dest_ip, dest_file)
        # proc = subprocess.Popen(['scp', filename, "%s@%s:%s" % (dest_uname, dest_ip, dest_file)])
        proc = subprocess.Popen(shlex.split(command))
        push_status = proc.wait()
        logger.debug("returned status %s", push_status)
        return push_status

    def pull_file(self, filename, source_uname, source_ip):
        """pull file 'filename' from the source"""
        my_file = Node.get_dest_path(filename, self.username)
        self.pulled_files.add(my_file)
        proc = subprocess.Popen(['scp', "%s@%s:%s" % (source_uname, source_ip, filename), my_file])
        return_status = proc.wait()
        logger.debug("returned status %s", return_status)

    def get_public_key(self):
        """Return public key of this client"""
        pubkey = None
        pubkey_dirname = os.path.join("/home", self.username, ".ssh")
        logger.debug("public key directory %s", pubkey_dirname)
        for tuple in os.walk(pubkey_dirname):
            dirname, dirnames, filenames = tuple
            break
        logger.debug("public key dir files %s", filenames)
        for filename in filenames:

            if '.pub' in filename:
                pubkey_filepath = os.path.join(dirname, filename)
                logger.debug("public key file %s", pubkey_filepath)
                pubkey = open(pubkey_filepath, 'r').readline()
                logger.debug("public key %s", pubkey)

        return pubkey

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

    def format_file_name(self, file_name):
        """
        Remove dir in full path of file
        author: daidv
        :param file_name:
        :return:
        """
        if file_name:
            for di in self.watch_dirs:
                if di in file_name:
                    return file_name.replace(di, '')
        else:
            return None

    def sync_files(self):
        """Sync all the files present in the mfiles set and push this set"""
        mfiles = self.mfiles
        while True:
            try:
                time.sleep(10)
                for filedata in mfiles.list():
                    filename = filedata.name
                    if not filename:
                        continue
                    logger.info("push filedata object to server %s", filedata)
                    server_uname, server_ip, server_port = self.server
                    # Add by daidv, only send file name alter for full path file to server
                    filedata.name = self.format_file_name(filedata.name)

                    dest_file = rpc.req_push_file(server_ip, server_port, filedata, self.username, self.ip, self.port)
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

    def watch_files(self):
        """keep a watch on files present in sync directories"""
        ob = Observer()
        # watched events
        ob.schedule(Handler(self.mfiles, self.rfiles, self.pulledfiles), self.watch_dirs)
        ob.start()
        logger.debug("watched dir %s", self.watch_dirs)
        # for watch_dir in self.watch_dirs:
        #     wm.add_watch(os.path.expanduser(watch_dir), mask, rec=False, auto_add=True)
        try:
            while True:
                time.sleep(5)
        except:
            self.ob.stop()
            print "Error"

    def mark_presence(self):
        server_uname, server_ip, server_port = self.server
        logger.debug("client call to mark available to the server")
        rpc.mark_presence(server_ip, server_port, self.ip, self.port)
        logger.debug("find modified files")

    def activate(self):
        """ Activate Client Node """
        super(Client, self).activate()
        self.watch_files()
        self.mark_presence()
        self.find_modified()
