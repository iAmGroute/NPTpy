#!/usr/bin/python3
python = 3
python

import time
import logging
logging.basicConfig(format='%(created).3f [%(name)s]\t%(message)s', level=20)

from Portal.Portal import Portal

ServerAddr = '192.168.11.1'
ServerPort = 4020

p = Portal(b'ABCE', ServerPort, ServerAddr)

while True:
    # print(p.links)
    p.main()

