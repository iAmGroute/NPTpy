# Unified server for managing portals (KA) & connections to relay server.

import logging
import socket
import threading
import socketserver

log = logging.getLogger(__name__)

class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):

    def handle(self):
        myName = threading.currentThread().name

        data = self.request.recv(64)
        portalID = data[0:4]

        log.info('[{0}] Request from: [{1}]:{2}'.format(myName, *self.request.getpeername()))
        log.info('[{0}]     with portalID: x{1}'.format(myName, portalID.hex()))

        # TODO: authenticate

        self.request.sendall(data)

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass


def client(ip, port, message):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((ip, port))
    try:
        sock.sendall(bytes(message, 'utf-8'))
        response = str(sock.recv(64), 'utf-8')
        print('Received: {}'.format(response))
    finally:
        sock.close()


if __name__ == '__main__':
    logging.basicConfig(format='%(created).3f [%(name)s|%(levelname)s] %(message)s', level=logging.INFO)

    HOST, PORT = '0.0.0.0', 0
    server = ThreadedTCPServer((HOST, PORT), ThreadedTCPRequestHandler)
    ip, port = server.server_address
    print(ip, port)
    ip = '127.0.0.1'

    # Start a thread with the server -- that thread will then start one
    # more thread for each request
    server_thread = threading.Thread(target=server.serve_forever)
    # Exit the server thread when the main thread terminates
    server_thread.daemon = True
    server_thread.start()
    print('Server loop running in thread:', server_thread.name)

    client(ip, port, 'Hello World 1')
    client(ip, port, 'Hello World 2')
    client(ip, port, 'Hello World 3')

    server.shutdown()
    server.server_close()
