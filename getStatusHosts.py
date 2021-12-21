#!/usr/bin/python3
import os

sdir = "/tmp/NGN/hosts"
if os.path.exists(sdir):
	files = sorted(os.listdir(sdir), key=lambda x: (len(x), x))
	for f in files:
		fp = sdir + "/" + f
		if os.path.isfile(fp):
			file = open(fp, 'r')
			print(f"{f} is {file.read()}")
			file.close()
else:
	print("Mininet network is not operational")
