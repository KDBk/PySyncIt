from SimpleXMLRPCServer import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler
import logging
import os
import re
import subprocess
import threading


__author__ = 'dushyant'
__updater__ = 'daidv'


logger = logging.getLogger('syncIt')


class Handler(SimpleXMLRPCRequestHandler):
    def _dispatch(self, method, params):
        try:
            print self.server.funcs.items()
            return self.server.funcs[method](*params)
        except:
            import traceback
            traceback.print_exc()
            raise


class Node(object):
    """Base class for client and server"""

    def __init__(self, role , ip, port, username, password, watch_dirs):
        self.role = role
        self.ip = ip
        self.port = int(port)
        self.username = username
        self.passwd = password
        self.watch_dirs = watch_dirs

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

    @staticmethod
    def get_dest_path(filename, dest_uname):
        """ Replace username in filename with 'dest_uname'"""
        user_dir_pattern = re.compile("/home/[^ ]*?/")

        if re.search(user_dir_pattern, filename):
            destpath = user_dir_pattern.sub("/home/%s/" % dest_uname, filename)
        logger.debug("destpath %s", destpath)
        return destpath

    @staticmethod
    def push_file(filename, dest_uname, dest_ip):
        """push file 'filename' to the destination """
        proc = subprocess.Popen(['scp', filename, "%s@%s:%s" % (dest_uname, dest_ip, Node.get_dest_path(filename, dest_uname))])
        return_status = proc.wait()
        logger.debug("returned status %s",return_status)

    def ensure_dir(self):
        """create directories to be synced if not exist"""
        for dir in self.watch_dirs:
            if not os.path.isdir(dir):
                os.makedirs(dir)

    def start_server(self):
        """Start RPC Server on each node """
        server = SimpleXMLRPCServer(("0.0.0.0", self.port), allow_none =True)
        server.register_instance(self)
        server.register_introspection_functions()
        rpc_thread = threading.Thread(target=server.serve_forever)
        rpc_thread.setDaemon(True)
        rpc_thread.start()
        logger.debug("server functions on rpc %s", server.funcs.items())
        logger.info("Started RPC server thread. Listening on port %s..." , self.port)


    def start_sync_thread(self):
        sync_thread = threading.Thread(target=self.sync_files)
        sync_thread.setDaemon(True)
        sync_thread.start()
        logger.info("Thread 'syncfiles' started ")

    def activate(self):
        self.ensure_dir()
        self.start_sync_thread()
        self.start_server()

