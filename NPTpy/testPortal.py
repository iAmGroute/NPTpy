#!/usr/bin/python3
python = 3
python

import time
import logging
logging.basicConfig(format='%(created).3f [%(name)s]\t%(message)s', level=logging.INFO)

from Portal.Portal import Portal

ServerAddr = 'k0.servers.netport.io'
ServerPort = 4020

p = Portal(b'ABCE', ServerPort, ServerAddr)

while True:
    # print(p.links)
    p.main()

