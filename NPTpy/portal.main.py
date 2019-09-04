
import time
import logging
import threading

from Portal.PortalConfig import PortalConfig
from Portal.PortalAPI    import PortalAPI
from Common.SimpleServer import SimpleServer

portalConfig = PortalConfig('portal.config.json')
portalConfig.save()

logging.basicConfig(format='%(created).3f [%(name)s]\t%(message)s', level=20)

while True:

    try:

        p = portalConfig.build()

        api = PortalAPI(p)
        server = SimpleServer(None, api)
        threading.Thread(target=server.run, args=(8000,), daemon=True).start()

        while True:
            p.main()

    except KeyboardInterrupt:
        break

    except Exception as e:
        logging.exception(e)

    time.sleep(10)

