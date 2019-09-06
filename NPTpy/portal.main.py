
import time
import logging
import threading
import gc

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
            # For some reason gc doesn't handle deletions
            # initiated by the other (API) thread,
            # so we'll periodically check here, to gc deleted sockets.
            gc.collect()

    except KeyboardInterrupt:
        break

    except Exception as e:
        logging.exception(e)

    time.sleep(10)

