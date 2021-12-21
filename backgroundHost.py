#!/usr/bin/python3
import controllerHost
import sys
from datetime import datetime

host = sys.argv[1]
status = controllerHost.get_status(host)
print(f"{host} is currently {status}")
controllerHost.ipt_roules(status)
print("--- Listening ---")
print(str(datetime.now()) + '\n', flush=True)

while True:
	controllerHost.get_magic_packet()
	print(str(datetime.now()) + '\n', flush=True)
