import os
import shutil
import sys
import time
import math

from controllerHost import get_status
from mininet.log import output, error
from mininet.cli import CLI
from mininet.log import setLogLevel
from mininet.net import Mininet
from mininet.topo import Topo
from mininet.node import RemoteController, OVSSwitch


SDIR = "/tmp/NGN/hosts"
TONULL = "&>/dev/null"
DHCP = False
S = 4
H = 12
hosts = []
switches = []

if len(sys.argv) > 1:
    for i in range(1, len(sys.argv)):
        try:
            if sys.argv[i] == '-s':
                S = int(sys.argv[i+1])
            elif sys.argv[i] == '-h':
                H = int(sys.argv[i+1])
            elif sys.argv[i] == '-dhcp':
                DHCP = True
            elif (not int(sys.argv[i])) or int(sys.argv[i]) > 99:
                raise Exception
        except:
            print("Invalid arguments")
            exit(-1)


# Override function ping for dhcp and check status
class Mininet(Mininet):
    def ping(self, hosts=None, timeout=None):
        """Ping between all specified hosts.
           hosts: list of hosts
           timeout: time to wait for a response, as string
           returns: ploss packet loss percentage"""
        # should we check if running?
        packets = 0
        lost = 0
        ploss = None
        if not hosts:
            hosts = self.hosts
            output('*** Ping: testing ping reachability\n')
        for node in hosts:
            if get_status(str(node.name)) == 'UP':
                output('%s -> ' % node.name)
                for dest in hosts:
                    if node != dest:
                        opts = ''
                        if timeout:
                            opts = '-W %s' % timeout
                        if dest.intfs:
                            # If DHCP is not running, get IP hardcoded
                            if not DHCP:
                                pdest = dest.IP()
                            else:
                                pdest = dest.name
                            result = node.cmd('LANG=C ping -c1 %s %s' %
                                              (opts, pdest))
                            sent, received = self._parsePing(result)
                        else:
                            sent, received = 0, 0
                        packets += sent
                        if received > sent:
                            error('*** Error: received too many packets')
                            error('%s' % result)
                            node.cmdPrint('route')
                            exit(1)
                        lost += sent - received
                        output(('%s ' % dest.name) if received else 'X ')
                output('\n')
            else:
                output('%s -> DOWN\n' % node.name)
        if packets > 0:
            ploss = 100.0 * lost / packets
            received = packets - lost
            output("*** Results: %i%% dropped (%d/%d received)\n" %
                   (ploss, received, packets))
        else:
            ploss = 0
            output("*** Warning: No packets sent\n")
        return ploss


class Topology(Topo):

    def build(self):
        global hosts, switches
        print(f"Starting the newtork with {H} hosts and {S} switches")
        for i in range(1, H+1):
            if DHCP:
                tmp = self.addHost(f'h{i}', ip=None)
            else:
                tmp = self.addHost(f'h{i}')
            hosts.append(tmp)
            print(f"Host h{i} created")
        for i in range(1, S+1):
            tmp = self.addSwitch(f's{i}')
            switches.append(tmp)
            print(f"Switch s{i} created")

        d = math.ceil(H/S)
       
        print(f"{d} Host per Switch")

        count = 0
        h_index = 0
        s_index = 0

        for i in range(0, H):

            if count < d and s_index < S:
                print(f"1 h_index {i} s_index {s_index} d {d} count {count}")
                self.addLink(hosts[i], switches[s_index])
                count += 1
            elif count == d:
                print(f"2 h_index {i} s_index {s_index+1} d {d} count {count}")
                self.addLink(hosts[i], switches[s_index+1])
                s_index += 1
                count = 1
            elif s_index == S:
                print(f"3 h_index {i} s_index {s_index} d {d} count {count}")
                self.addLink(hosts[i], switches[s_index])

        for i in range(1, S-1):
            if i == 1:
                self.addLink(switches[i], switches[i-1])
            self.addLink(switches[i], switches[i+1])

        print("*** Setting files and directories")
        os.umask(0000)
        if os.path.exists(SDIR):
            shutil.rmtree(SDIR)
        os.makedirs(f"{SDIR}/LOGs")
        os.environ["statusdir"] = SDIR

        for h in hosts:
            host = str(h)
            fileS = f"{SDIR}/{host}"
            fileL = f"{SDIR}/LOGs/{host}.log"
            # Set status file
            try:
                os.close(os.open(fileL, os.O_CREAT | os.O_WRONLY, 0o777))
                f = open(os.open(fileS, os.O_CREAT | os.O_WRONLY, 0o777), 'w')
                if host == "h1":
                    # Only h1 stars UP
                    f.write("UP")
                else:
                    f.write("DOWN")
                f.close()
            except OSError:
                print("Failed creating files")
            else:
                print(f"Files of host {host} created")


def runTopo():
    topo = Topology()
    net = Mininet(topo=topo,
        controller=lambda name: RemoteController(name, ip='127.0.0.1'),
        switch=OVSSwitch,
        autoSetMacs=True)

    net.start()
    node1 = net.getNodeByName("s1")
    print("*** Setting up bridge network")
    node1.cmd('sudo ovs-vsctl add-port s1 eth1')
    if DHCP:
        print("*** Setting up correctly resolv.conf ***")
        os.system("sudo /usr/bin/bash util/resolved.sh")
    print("*** Executing background scripts and dhcp request (if needed)")
    for h in net.hosts:
        if DHCP:
            # Unable to modify config file for evey host, so change temporary hostname
            h.cmd(f"hostname {str(h)}")
            h.cmd(f"dhclient -4")  # +h.defaultIntf().name #-e HOST={str(h)} -cf ./configs/mn_dhclient.conf
        # With parantesesis invade the mininet terminal of single host and get signals
        h.cmd(f"python3 backgroundHost.py {str(h)} > {SDIR}/LOGs/{str(h)}.log &")
        # Start script slowly because jumps host if faster
        time.sleep(0.1)
        # net.terms += makeTerm(h, f"Background script on {str(h)}", cmd=f"python3 backgroundHost.py {str(h)}")
        print(f"Started {str(h)} script")
    print("All scripts started")
    node1.cmd("hostname comnetsemu")

    CLI(net)

    # After the user exits the CLI, shutdown the network.
    net.stop()
    shutil.rmtree(SDIR)
    if DHCP:
        os.system("sudo /usr/bin/bash util/resolved_restore.sh")


if __name__ == '__main__':
    # This runs if this file is executed directly
    setLogLevel('info')
    runTopo()
