#!/bin/bash
PID=`ps -fu root | awk '/delcia_web.py/ && !/awk/ {print $2}'`

if [[ -z "$PID" ]]; then
  echo "Delcia web is not running"
else
  echo "Delcia web is running at pid $PID"
  kill -9 $PID
fi
