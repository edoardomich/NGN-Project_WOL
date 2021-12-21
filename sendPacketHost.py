#!/usr/bin/python3
import controllerHost

host = controllerHost.get_hostname()
if controllerHost.get_status(host) == "UP":
	controllerHost.send_packet(None)
else:
	print(f"Current host ({host}) is DOWN and cannot send any packet")
