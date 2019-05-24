python = 3
python

import time
import logging
logging.basicConfig(format='%(created).3f [%(name)s]\t%(message)s', level=logging.INFO)

from Servers.Relay import Relay

r = Relay(4021)

while True:
    print(r.tokenMap)
    r.main()

