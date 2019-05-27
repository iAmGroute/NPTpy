
import ssl

from .Connector import *

# TODO:
# add more secure options to SSLContext

class SecureClientConnector(Connector):

    def secure(self, serverHostname, caFilename=None, caDirpath=None, caData=None):
        self.sslContext = ssl.create_default_context(cafile=caFilename, capath=caDirpath, cadata=caData)
        self.socket     = self.sslContext.wrap_socket(self.socket, server_hostname=serverHostname)


class SecureServerConnector(Connector):

    def secure(self, certFilename, keyFilename=None, keyPassword=None):
        self.sslContext          = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        self.sslContext.options |= ssl.OP_NO_TLSv1
        self.sslContext.options |= ssl.OP_NO_TLSv1_1
        self.sslContext.load_cert_chain(certFilename, keyFilename, keyPassword)
        self.socket = self.sslContext.wrap_socket(self.socket, server_side=True)

