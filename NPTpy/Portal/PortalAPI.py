
import time

class PortalAPI:

    def __init__(self, myPortal):
        self.myPortal = myPortal
        self.bootID   = time.time()

    def process(self, context, data):
        result           = serializePortal(self.myPortal)
        result['bootID'] = self.bootID
        result['time']   = time.time()
        return result

def serializePortal(portal):
    p = portal
    r = {}
    r['portalID']    = p.portalID.hex().upper()
    r['serverPort']  = p.serverPort
    r['serverAddr']  = p.serverAddr
    r['port']        = p.port
    r['address']     = p.address
    r['links']       = [ {'k': i.myID, 'v': serializeLink(i) } for i in p.links ]
    r['allowSelect'] = p.allowSelect
    return r

def serializeLink(link):
    l = link
    r = {}
    r['isClient']     = l.isClient
    # r['myID']         = l.myID
    r['otherID']      = l.otherID.hex().upper()
    r['rtPort']       = l.rtPort
    r['rtAddr']       = l.rtAddr
    r['ltPort']       = l.ltPort
    r['ltAddr']       = l.ltAddr
    r['listeners']    = [ {'k': i.myID, 'v': serializeListener(i) } for i in l.listeners ]
    r['eps']          = [ {'k': i.myID, 'v': serializeEndpoint(i) } for i in l.eps ]
    r['buffer']       = l.buffer.hex().upper()
    r['state']        = l.state.name
    r['allowSelect']  = l.allowSelect
    r['waitingSince'] = l.waitingSince
    return r

def serializeListener(listener):
    l = listener
    r = {}
    # r['myID']        = l.myID
    r['remotePort']  = l.remotePort
    r['remoteAddr']  = l.remoteAddr
    r['localPort']   = l.localPort
    r['localAddr']   = l.localAddr
    r['allowSelect'] = l.allowSelect
    r['reserveID']   = l.reserveID
    return r

def serializeEndpoint(endpoint):
    e = endpoint
    r = {}
    # r['myID']        = e.myID
    r['myIDF']       = e.myIDF
    r['allowSelect'] = e.allowSelect
    return r

