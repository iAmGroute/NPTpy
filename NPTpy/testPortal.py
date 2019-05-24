python = 3
python

import time
import logging
logging.basicConfig(format='%(created).3f [%(name)s]\t%(message)s', level=logging.INFO)

from Portal.Portal import Portal

p = Portal(b'ABCE')

while True:
    # print(p.links)
    p.main()

