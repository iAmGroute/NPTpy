python = 3
python

import time
import logging
logging.basicConfig(format='%(created).3f [%(name)s|%(levelname)s] %(message)s', level=logging.INFO)

from Servers.Server import Server

s = Server(4020)

while True:
    print(s.portalIndexer)
    s.main()

