
import time
import logging

from PortalConfig import PortalConfig

portalConfig = PortalConfig('portal.config.json')
portalConfig.save()

logging.basicConfig(format='%(created).3f [%(name)s]\t%(message)s', level=20)

while True:

    try:

        p = portalConfig.build()

        while True:
            p.main()

    except KeyboardInterrupt:
        break

    except Exception as e:
        logging.exception(e)

    time.sleep(10)

