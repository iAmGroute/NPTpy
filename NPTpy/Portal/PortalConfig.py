
import json
import time

import ConfigFields          as CF
import Common.ConfigVerifier as CV

from Portal.Portal import Portal

configTemplate = {
    'Note': [
        'This is the configuration for the NetPort Portal.',
        'You can read more about it here: https://netport.io/portal'
    ],
    'PortalID': CF.PortalID('00000000'),
    'Links': [{
        'OtherID': CF.PortalID('00000000'),
        'Listeners': [{'RP': CF.Port(0), 'RA': CF.Address(''), 'LP': CF.Port(0), 'LA': CF.Address('')}]
    }],
    'Logs': {
        'stateChanges':        CF.Log( True),
        'outgoingConnections': CF.Log( True),
        'acceptIncoming':      CF.Log( True),
        'declineIncoming':     CF.Log( True),
        'closeExceptions':     CF.Log( True),
        'TCPsendExceptions':   CF.Log( True),
        'TCPrecvExceptions':   CF.Log( True),
        'UDPsendExceptions':   CF.Log( True),
        'UDPrecvExceptions':   CF.Log( True),
        'TCPcontent':          CF.Log(False),
        'UDPcontent':          CF.Log(False)
    },
    'PortsToTry': [CF.Port(0)],
    'Servers': [CF.Address('')]
}
verifier = CV.getVerifier(configTemplate)

class PortalConfig:

    def __init__(self, fileName):
        self.fileName = fileName
        self.config   = None
        self.read()

    def readAndBuild(self):
        self.read()
        return self.build()

    def scanAndSave(self, portal):
        self.scan(portal)
        return self.save()

    def read(self):

        with open(self.fileName, 'r') as f:
            data = f.read()

        try:
            self.config = verifier.apply(json.loads(data))
            print(self.config)

        except json.decoder.JSONDecodeError:

            bakName = self.fileName[:self.fileName.rfind('.')] + str(int(time.time())) + '.json'

            print('Error: configuration file was not valid and will be renamed to ' + bakName)
            with open(bakName, 'w') as f2:
                f2.write(data)


    def save(self):
        with open(self.fileName, 'w') as f:
            f.write(json.dumps(self.config, indent=4, sort_keys=False) + '\n')


    def build(self):

        config = self.config

        portalID   = bytes.fromhex(config['PortalID'])
        serverPort = config['PortsToTry'][0]
        serverAddr = config['Servers'][0]

        p = Portal(portalID, serverPort, serverAddr)

        for linkConf in config['Links']:

            otherID = bytes.fromhex(linkConf['OtherID'])

            link = p.createLink(True, otherID)

            for listenerConf in linkConf['Listeners']:
                link.addListener(listenerConf['RP'], listenerConf['RA'], listenerConf['LP'], listenerConf['LA'])

        return p


    def scan(self, portal):

        config = {}

        config['PortalID']   = portal.portalID.hex().upper()
        config['PortsToTry'] = [portal.serverPort]
        config['Servers']    = [portal.serverAddr]

        config['Links'] = [
            {
                'OtherID': link.otherID.hex().upper(),
                'Listeners': [
                    { 'RP': listener.remotePort, 'RA': listener.remoteAddr, 'LP': listener.localPort, 'LA': listener.localAddr }
                    for listener in link.listeners
                ]
            }
            for link in portal.links if link.isClient
        ]

        self.config = config

