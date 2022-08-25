#!/bin/bash
if [[ -z "${DELCIA_DIR}" ]]; then
  DELCIA_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
fi
cd $DELCIA_DIR
PID=`ps -fu root | awk '/delcia_web.py/ && !/awk/ {print $2}'`

if [[ -z "$PID" ]]; then
  echo "Starting Delcia web"
  exec $DELCIA_DIR/delcia_web_deamon.sh
else
  echo "Delcia web is running at pid $PID"
fi