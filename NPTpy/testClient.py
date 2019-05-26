#!/usr/bin/python3
python = 3
python

import time
import logging
logging.basicConfig(format='%(created).3f [%(name)s]\t%(message)s', level=logging.INFO)

from Portal.Portal import Portal

ServerAddr = 'k0.servers.netport.io'
ServerPort = 4020

c = Portal(b'ABCF', ServerPort, ServerAddr)

c.main()

c.connectToPortal(b'ABCE')

c.main()


c.main()

c.links[0].addListener(5201, '192.168.11.11', 1234, '0.0.0.0')

while True:
    # print(c.links[0].eps)
    c.main()

