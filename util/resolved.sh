#!/usr/bin/env bash

echo "Stopping systemd-resolved.service"
systemctl stop systemd-resolved.service;

echo "Disabling systemd-resolved.service"
systemctl disable systemd-resolved.service;

RFILE='/etc/resolv.conf';
if [[ -L "$RFILE" ]]
then
  echo "Removing symlink to /run/systemd/resolve/stub-resolv.conf"
  $(mv $RFILE $RFILE.org);
  $(echo "# NGN Project" > $RFILE);
fi
