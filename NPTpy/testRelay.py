#!/usr/bin/python3
python = 3
python

import time
import logging
logging.basicConfig(format='%(created).3f [%(name)s]\t%(message)s', level=logging.INFO)

from Servers.Relay import Relay

r = Relay(4021, '0.0.0.0', 40401, '127.0.0.1')

while True:
    print(r.tokenMap)
    r.main()

