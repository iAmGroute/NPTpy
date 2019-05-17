python = 3
python

import time
import logging
logging.basicConfig(format='%(created).3f [%(name)s|%(levelname)s] %(message)s', level=logging.INFO)

from Portal import Portal

c = Portal(b'ABCF')

c.main()

c.connectToPortal(b'ABCE')

c.main()

c.conRTs[0].mode = c.conRTs[0].Modes.Client

c.main()
c.main()

data = (8080).to_bytes(2, 'little')
data += b'192.168.11.11'

c.conRTs[0].sendall(data)

while True:
    print(c.conRTs)
    c.main()

