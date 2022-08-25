#!/bin/sh
env >> /etc/environment
python3 delcia_web.py > log.txt 2>&1 &
crond -f -l 2
