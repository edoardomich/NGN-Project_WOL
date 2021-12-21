#!/usr/bin/env bash

RFILE='/etc/resolv.conf';
if [[ -e "$RFILE" ]]
then
  $(rm $RFILE)
fi

echo "Restoring symlink to /run/systemd/resolve/stub-resolv.conf"
$(mv $RFILE.org $RFILE)

echo "Starting systemd-resolved.service"
systemctl start systemd-resolved.service;

echo "Enabling systemd-resolved.service"
systemctl enable systemd-resolved.service;
