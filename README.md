
# Netport client implementation in Python

Netport is a port-based, IOT-oriented, secure network tunneling project.  
It enables communication across private networks, where firewalls or [NATs](https://en.wikipedia.org/wiki/Network_address_translation) may block incoming traffic.  
End-devices (*portals*) use publicly accessible servers and relays to establish an end-to-end TLS tunnel, over which the traffic is forwarded.  
Access is fine-grain, centrally controlled, and specified as pairs of port-address tuples.  
Authentication is based on X.509 certificates.  
It's operation is very similar to SSH port forwarding and functionality similar to some [overlay-network](https://en.wikipedia.org/wiki/Overlay_network)/[zero-trust](https://en.wikipedia.org/wiki/Zero_trust_security_model) systems ([ZeroTier](https://en.wikipedia.org/wiki/ZeroTier), [Nebula](https://github.com/slackhq/nebula), [Tailscale](https://github.com/tailscale/tailscale), [Twingate](https://www.twingate.com))   

## Architecture

```
  Client's private network |    Public Internet    |  Server's private network     
                           |                       |                               
         +----1----+       |                       |                               
         | client/ |-------|-----.   +----4----+   |                               
         | portal  |-------|--.  '-->| Netport |   |                               
         +---------+       |  |      |  Server |<--|---.                           
                           |  |  .-->|         |   |   |  +---6----+               
+---2----+     +---3----+  |  |  |   +----+----+   |   '--|        |    +---7----+ 
| client |---->| portal |--|-----'        |        |      | portal |--->| server | 
+--------+     +--+--+--+  |  |           V        |   .--|        |    +--------+ 
                  |  |     |  |      +----5----+   |   |  +--------+               
                  |  |     |  '----->| Netport |   |   |      ^                    
                  |  |     |         |  Relay  |<--|---'      |                    
                  |  '-----|-------->|  (XDP)  |   |          |                    
                  |        |         +---------+   |          |                    
                  |        |                       |          |                    
                  '--------|----------->-----------|----------'                    
```

- Applications on end-clients `1`, `2` want to connect to server `7`.
- Client `2` connects to portal `3` using TCP or UDP over a specified port.
- Client `1` runs a portal locally, so the application will connect to localhost instead.
- Portals `1` and `3` will ask Netport server `4` (outbound, over TCP/UDP ports 80, 443 or others)
  to provide a relay and notify portal `6` to connect to it.
- Netport server `4` picks relay `5`, asks it to establish a specific pair of listening ports.
  Then, it sends this information along with the relay's address to portals `1`/`3` and `6`.
- The relay creates a forwarding entry with these ports and performs packet forwarding (optionally using an eBPF/XDP program).
- The portals connect to the relay via TCP/UDP and establish a TLS tunnel.
- Portal `6` connects to the end-server `7`.
- Traffic is forwarded between the clients' connections to the server's connection over the TLS tunnel.
  The forwarding is transparent to the application.
- (Future expansion), the portals attempt to establish a direct connection (`3`->`6`) in the background.

#### Notes:
- Only the portal's code (`1,3,6`) is currently checked-in this repository.  
  I have yet to upload the server's and relay's code.
- UDP support is experimental.
- All processes can be run by regular users, except if required to listen on well-known TCP/UDP ports,  
  which is usually the case for the Netport Server and Relay.  
  Using the Relay with XDP requires root privileges or CAP_BPF.

#### Future expansion:
- Enhanced [NAT traversal](https://en.wikipedia.org/wiki/NAT_traversal),  
  with support for UPnP and [hole-punching](https://en.wikipedia.org/wiki/TCP_hole_punching).
- Local network and localhost [mDNS](https://en.wikipedia.org/wiki/Multicast_DNS) broadcasting.
- Latency-based congestion control.
- Portal-portal link [multipath](https://en.wikipedia.org/wiki/Multipath_routing).
- Unix socket support and possibly arbitrary sockets/streams (like/using [socat](https://linux.die.net/man/1/socat)).
- Certificate management, additional authentication methods/gateways.
- Automated deployment with Kubernetes.
