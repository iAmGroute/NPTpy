#!/usr/bin/python3
python = 3
python

import time
import logging
logging.basicConfig(format='%(created).3f [%(name)s]\t%(message)s', level=20)

from Portal.Portal import Portal

ServerAddr = '192.168.11.1'
ServerPort = 4020

c = Portal(b'ABCF', ServerPort, ServerAddr)

link = c.createLink(True, b'ABCE')
link.addListener(8080, '192.168.11.11', 1234, '0.0.0.0')

while True:
    # print(c.links)
    c.main()

