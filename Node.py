from SimpleXMLRPCServer import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler
import re
import subprocess
import threading

__author__ = 'dushyant'

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

    def __init__(self, role , ip, port, uname):
        self.role = role
        self.my_ip = ip
        self.port = int(port)
        self.my_uname = uname

    @staticmethod
    def getdestpath(filename, dest_uname):
        p = re.compile("(/home/[a-z]*/)")

        destpath = p.sub("/home/%s/" % dest_uname, filename)
        print "getdestpath" + destpath
        return destpath


    @staticmethod
    def pushfile(filename, dest_uname, dest_ip):
        """push file 'filename' to the destination """
        proc = subprocess.Popen(['scp', filename, "%s@%s:%s" % (dest_uname, dest_ip, Node.getdestpath(filename, dest_uname))])
        print proc.wait()


    def start_server(self):
        """ Start RPC Server on each node """
        server = SimpleXMLRPCServer(("0.0.0.0", self.port), allow_none =True)
        server.register_instance(self)
        server.register_introspection_functions()
#        rpc_thread = threading.Thread(target=server.serve_forever())
#        rpc_thread.start()
        print "server functions ", server.funcs.items()
        print self.__dict__
        print "Started RPC server thread. Listening on port %s..." % (self.port)
        server.serve_forever()

        #TODO add support to sync more folders

#    def add_folder(self, src):
#        """add src to the list of synced folders;Put a monitor on this too"""
