python = 3
python

import time
import logging
logging.basicConfig(format='%(created).3f [%(name)s|%(levelname)s] %(message)s', level=logging.INFO)

from Portal import Portal

p = Portal(b'ABCE')

while True:
    print(p.conRTs)
    p.main()

