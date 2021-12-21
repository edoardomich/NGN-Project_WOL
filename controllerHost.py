#!/usr/bin/python3
import os
import subprocess
import socket
import netifaces
import re

# Personal define of Ethernet Packet Type following /usr/include/linux/if_ether.h
ETH_P_WOL = 0x0842
WOL_SIZE = 116  # Size of WOL packet without optional headers
MAC_BROADCAST_B = bytes.fromhex("F" * 12)


def ipt_roules(status):
	# Get local ip
	ip = subprocess.check_output("hostname -I | awk '{print $1}'", shell=True).decode("utf-8")[:-1]

	if status == "DOWN":
		# Add Rule
		os.system("iptables -A INPUT -d " + ip + " -j REJECT 2> /dev/null")
		os.system("iptables -A OUTPUT -s " + ip + " -j REJECT 2> /dev/null")
	else:
		# Delete Rule
		os.system("iptables -D INPUT -d " + ip + " -j REJECT 2> /dev/null")
		os.system("iptables -D OUTPUT -s " + ip + " -j REJECT 2> /dev/null")

	print("IPTABLES rules updated")


def get_status(hostname):
	sdir = str(os.getenv("statusdir"))
	sfilep = sdir + "/" + hostname
	sfile = open(sfilep, 'r')
	status = sfile.read()
	sfile.close()
	return status


def set_status(hostname, status):
	sdir = str(os.getenv("statusdir"))
	sfilep = sdir + "/" + hostname
	sfile = open(sfilep, 'w')
	sfile.write(status)
	sfile.close()


def update_status(hostname):
	status = get_status(hostname)
	if status == "DOWN":
		status = "UP"
	elif status == "UP":
		status = "DOWN"
	else:
		print(hostname + " has an Invalid status")
		return

	set_status(hostname, status)
	ipt_roules(status)
	print(hostname + " is now " + status)


def check_mac(mac):
	return re.fullmatch(
		'^([A-F0-9]{2}(([:][A-F0-9]{2}){5}|([-][A-F0-9]{2}){5})|([\s][A-F0-9]{2}){5})|'
		'([a-f0-9]{2}(([:][a-f0-9]{2}){5}|([-][a-f0-9]{2}){5}|([\s][a-f0-9]{2}){5}))$',
		mac)


def get_mac_arp(hostname, dnssrv=False):
	try:
		ipaddr = socket.gethostbyname(hostname)
	except socket.gaierror:
		if not dnssrv:
			print("Error resolving hostname" + "\n"
						"Is DNS server running?")
			if input("Are you running mininet topology without DNS? [Y/N]: ").lower() == 'y':
				if re.fullmatch('^h\d+$', hostname) is not None:
					# Get index of the host and create MAC address from that with padding (MAX Host=255)
					macbytes = bytes([int(hostname.replace('h', ''))]).rjust(6, b'\x00')
					return macbytes, None
				else:
					print("Provided hostname is not a well formed mininet hostname")
					return None, None
			else:
				print("Provide full MAC address instead of hostname")
				return None, None
		else:
			print("Provided hostname is not know by DNS server")
			return None, None

	neigh = subprocess.check_output(f"ip neigh show {ipaddr}", shell=True).decode("utf-8")
	if re.search('lladdr ([a-f0-9]{2}([:][a-f0-9]{2}){5})', neigh) is not None:
		macaddr = re.search('lladdr ([a-f0-9]{2}([:][a-f0-9]{2}){5})', neigh).group(1)
		macbytes = bytes.fromhex(macaddr.replace(':', ''))
		return macbytes, macaddr
	else:
		return None, None


def request_intf(dnssrv=False):
	s = socket.socket(socket.AF_PACKET, socket.SOCK_RAW)
	# If DNSServer request this function don't ask which intf
	if (len(socket.if_nameindex()) > 2) and (dnssrv is False):
		for i in socket.if_nameindex():
			print(str(i[0]) + " -> " + i[1])
		idx = int(input("Choose the index of the interface where send the packet: "))
	else:
		# Speed up in best case scenarios, excluding loopback interface
		idx = 2
	interface = socket.if_indextoname(idx)

	return s, interface


def send_request_to_dnsserver(hostname):
	s, interface = request_intf()
	# Specification seams not working, only interfeace is necessary
	s.bind((interface, 0x1112, socket.PACKET_BROADCAST))
	data, hostname = create_dns_packet(s.getsockname()[4], hostname.encode('utf-16'))
	if data is not None:
		s.send(data)
	return


def get_request_to_dnsserver():
	# Funzione di ascolto per DNSServer
	s_rec = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(0x1112))
	# s_rec.bind((interface, 0)) # not necessary -> listening on all interfaces
	size = 255
	payload = s_rec.recv(size)
	hostname = payload.decode('utf-16')[8:].strip('\x00')

	mac_dst_bin, mac_dst = get_mac_arp(hostname, dnssrv=True)
	print("Request to wake host {} with mac {}".format(hostname, mac_dst))
	if mac_dst_bin is not None:
		# Send Packet without asking for the interface on DNSServer
		send_packet(mac_dst_bin, dnssrv=True)
	else:
		print("Hostname Incorrect")

	return


def create_packet(mac_src, machost_dst):
	eth_type = bytes.fromhex("1111")  # int -> 4369
	mac_dst = MAC_BROADCAST_B

	if machost_dst is None:
		wol_dst = input("Provide the hostname or complete MAC address\n"
										"(accepted separator separator [:-\]) of the machine to WOL: ")
		# Check mac address format
		addr = check_mac(wol_dst)
		# Match all posssibile hostname (no only numbers, space etc)
		hostname = re.fullmatch('^(?!\d*$)\w+\.*\w+$',	wol_dst)
		try:
			# 1 match, or the MAC is invalid
			if addr is not None:
				# Remove mac separator [:-\s] and convert to bytes
				data = bytes.fromhex(wol_dst.replace(wol_dst[2], ''))
			else:
				if hostname is None:
					raise ValueError('Incorrect MAC address format or hostname')
				elif hostname.group(0) == get_hostname():
					raise ValueError(f'{hostname.group(0)} is this host')
				else:
					# Return data=None as a flag to delegate DNSServer
					return None, wol_dst
		except ValueError as verr:
			print("Exception caught: "+repr(verr))
			exit(-1)

	else:
		data = machost_dst
	# The message is compose by the mac address of machine that would receive the WOL Magic Packet
	payload = mac_dst + mac_src + eth_type + data

	return payload, None


def create_dns_packet(mac_src, machost_dst):
	eth_type = bytes.fromhex("1112")
	mac_dst = MAC_BROADCAST_B
	data = machost_dst
	# The message is compose by the mac address of machine that would receive the WOL Magic Packet
	payload = mac_dst + mac_src + eth_type + data

	return payload, None


def send_packet(mac_dst, dnssrv=False):
	s, interface = request_intf(dnssrv)
	# Specification seams not working, only interfeace is necessary
	s.bind((interface, 0x1111, socket.PACKET_BROADCAST))
	data, hostname = create_packet(s.getsockname()[4], mac_dst)
	# Check if the 0x1111 packet is delegated to DNSServer
	if data is not None:
		s.send(data)
	else:
		# Trying to get mac from local arp
		h = get_mac_arp(hostname)[0]
		if h is not None:
			send_packet(h)
		else:
			# Delegate DNSServer
			send_request_to_dnsserver(hostname)


def check_packet(data) -> bool:
	res = False
	for i in netifaces.interfaces():
		i_mac = str(netifaces.ifaddresses(i)[netifaces.AF_LINK][0].get('addr')).replace(':', '')
		if data[0:6].hex() == i_mac:
			mac_src = data[6:12].hex(':')
			if check_mac(mac_src):
				if int.from_bytes(data[12:14], "big") == ETH_P_WOL:
					if data[14:20] == MAC_BROADCAST_B:
						if data[20:].hex() == i_mac*16:
							print("Packet received on " + i + " interface from " + mac_src)
							res = True

	return res


def get_hostname() -> str:
	ifaces = netifaces.interfaces()
	# Check the nuber of host (of mininet)
	hostname = re.search('^(h\d+)-eth0$', ifaces[1]).group(1)
	if hostname != "":
		return hostname
	else:
		print("Error recognising hostname")


def get_magic_packet():
	s_rec = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(ETH_P_WOL))
	# s_rec.bind((interface, 0)) # not necessary -> listening on all interfaces
	size = WOL_SIZE
	payload = s_rec.recv(size)
	if check_packet(payload):
		hostname = get_hostname()
		if hostname != "":
			update_status(hostname)
		else:
			print("Error recognising hostname")

# END
