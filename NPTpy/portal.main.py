
import time
import logging

from PortalConfig  import PortalConfig
from Portal.Portal import Portal

portalConfig = PortalConfig('portal.config.json')
portalConfig.save()
config       = portalConfig.config

logging.basicConfig(format='%(created).3f [%(name)s]\t%(message)s', level=20)

ServerAddr = config['Servers'][0]
ServerPort = config['PortsToTry'][0]
PortalID   = bytes.fromhex(config['PortalID'])

while True:

    try:

        p = Portal(PortalID, ServerPort, ServerAddr)

        for linkConf in config['Links']:
            link = p.createLink(True, bytes.fromhex(linkConf['OtherID']))
            for listenerConf in linkConf['Listeners']:
                link.addListener(listenerConf['RP'], listenerConf['RA'], listenerConf['LP'], listenerConf['LA'])

        while True:
            p.main()

    except KeyboardInterrupt:
        break

    except Exception as e:
        logging.exception(e)

    time.sleep(10)

