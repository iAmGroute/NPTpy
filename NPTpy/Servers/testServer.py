python

import time
import logging
logging.basicConfig(format='%(created).3f [%(name)s|%(levelname)s] %(message)s', level=logging.INFO)

from Servers.Server import Server

s = Server(4020)

s.task()

s.task()

print(s.portalTable)
print(s.portalIndexer)

s.process(s.portalTable[0].conn)
