
import time
import logging
import threading
import gc
import sys
import webbrowser

from Portal.PortalConfig import PortalConfig
from Portal.PortalAPI    import PortalAPI
from Common.SimpleServer import SimpleServer

portalConfig = PortalConfig('portal.config.json')
portalConfig.save()

logging.basicConfig(stream=sys.stdout, format='%(created).3f [%(name)s]\t%(message)s', level=20)

webbrowser.open('http://127.0.0.1:8000')

while True:

    try:

        p = portalConfig.build()

        api = PortalAPI(p, portalConfig)
        server = SimpleServer('webui', api)
        s = threading.Thread(target=server.run, args=(8000, '0.0.0.0'), daemon=True)
        s.start()

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

    server.stop()
    s.join()
    del s
    del server
    del api
    del p
    gc.collect()
    time.sleep(10)

