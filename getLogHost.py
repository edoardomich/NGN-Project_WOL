#!/usr/bin/python3
import os

sdir = "/tmp/NGN/hosts/LOGs"
if os.path.exists(sdir):
	f = input("Indicate the host of which you want see the log: ")
	fp = f"{sdir}/{f}.log"
	if os.path.isfile(fp):
		file = open(fp, 'r')
		lines = file.readlines()
		print("--- Last 15 lines ---")
		for l in lines[-15:]:
			print(l, end="")
		file.close()
else:
	print("Mininet network is not operational")
