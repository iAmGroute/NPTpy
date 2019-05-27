#!/usr/bin/python3
python = 3
python

import time
import logging
logging.basicConfig(format='%(created).3f [%(name)s]\t%(message)s', level=logging.INFO)

from Portal.Portal import Portal

ServerAddr = '192.168.11.1'
ServerPort = 4020

c = Portal(True, b'ABCF', ServerPort, ServerAddr)

c.main()

c.connectToPortal(b'ABCE')

c.main()


c.main()

c.links[0].addListener(5201, '192.168.11.11', 1234, '0.0.0.0')

while True:
    # print(c.links[0].eps)
    c.main()

