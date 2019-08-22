
import json
import time

import ConfigFields          as CF
import Common.ConfigVerifier as CV

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
    'Servers': [CF.Address('')],
    'PortsToTry': [CF.Port(0)]
}
verifier = CV.getVerifier(configTemplate)

class PortalConfig:

    def __init__(self, fileName):
        self.fileName = fileName
        self.config   = None
        self.read()

    def read(self):
        with open(self.fileName, 'r') as f:
            data = f.read()
        try:
            self.config = verifier.apply(json.loads(data))
        except json.decoder.JSONDecodeError:
            bakName = self.fileName[:self.fileName.rfind('.')] + str(int(time.time())) + '.json'
            print('Error: configuration file was not valid will be renamed to ' + bakName)
            with open(bakName, 'w') as f2:
                f2.write(data)

    def save(self):
        with open(self.fileName, 'w') as f:
            f.write(json.dumps(self.config, indent=4, sort_keys=False) + '\n')

