#!/usr/bin/python3
python = 3
python

import time
import logging
logging.basicConfig(format='%(created).3f [%(name)s]\t%(message)s', level=logging.INFO)

from Servers.Server import Server

RelayAddr = 'r0.servers.netport.io'
RelayPort = 4021
RelayManageAddr = '127.0.0.1'
RelayManagePort = 40401

s = Server(4020, '0.0.0.0', 0, '127.0.0.1', RelayPort, RelayAddr, RelayManagePort, RelayManageAddr)

while True:
    print(s.portalIndexer)
    s.main()

