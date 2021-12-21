# NGN Project - PC Wake-on-LAN manager
## How to run the project ##
- Connect dhcp/dns to comnetsemu's eth1 (optional)
  - Execute backgroundDNSServer.py on dhcp/dns server
- ryu-manager ryu_controller.py
- sudo python3 network.py [-s][-h][-dhcp]

All the executions for commands in mininet (and hosts xterm) must be run without 'sudo' prefix.


## How to wakeup / shutdown hosts ##
On a mininet's child node execute "sendPacketHost.py" and specify mac-address or hostname.

If mininet topology is started with -dhcp option and the "backgroundDNSServer.py" is running hostname specified will wake up.
Without the listener on DNS server, the hostname provided cannot be resolved, therefore only with complete MAC address
the sleeping host will wake up.

If mininet topology is started without -dhcp option, mininet standard hostnames (hxx) can be still provided and resolved.

## How to get information ##
Even if you can't ping down hosts you can still use "getStatusHost.py" to get the status of every host of the mininet network.

With "getLogHost.py" you can see the history on activities of the provided host.


## Limitations ##
Maximum number of hosts is:
- 99 (with dhcp)
- 255 (within mininet)

Minimum number of switches is 1.

If you stop manually mininet script when DHCP requests of the mininet hosts are running,
restore machine hostname with "sudo hostname HOSTNAME" after mininet cleanup (mn -c).


## Known Problems ##
On a fresh comnetsemu machine, the first time you try executing any ryu script it'll throw "Already Handled" exception. In this case you'll just need to run "pip install eventlet==0.30.2" and restart the ryu script. If you are stuck with the DNS configuration from the project (due to premature exit from mininet) and can't reach internet just edit (or create) the file /etc/resolv.conf and as the first line "nameserver 8.8.8.8".

Rarely the error "Unsupported version 0x1" could pop up in ryu console. Just stop ryu and mininet and perform a mininet clear with "sudo mn -c".

## Other ##
In the 'configs' directory there is the 'dnsmasq.conf' file used in our dhcp/dns server.
