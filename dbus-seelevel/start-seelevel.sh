#!/bin/bash

# remove comment for easier troubleshooting
#set -x

. /opt/victronenergy/serial-starter/run-service.sh

# start -x -s $tty
app="python /data/apps/dbus-seelevel/dbus-seelevel.py"
args="/dev/$tty"
start $args
