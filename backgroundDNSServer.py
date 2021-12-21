#!/usr/bin/python3
import controllerHost
import os
from datetime import datetime

print("--- Applying Setting ---")
# Restart dnsmasq service
os.system("systemctl restart dnsmasq.service")

print("--- Listening ---")
print(str(datetime.now()) + '\n', flush=True)
while True:
	controllerHost.get_request_to_dnsserver()
	print("Destination host received, forward the creation of personal packet")
	print(str(datetime.now()) + '\n', flush=True)

