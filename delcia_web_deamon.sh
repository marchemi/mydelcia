#!/bin/bash
if [[ -z "${DELCIA_DIR}" ]]; then
  DELCIA_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
fi
cd $DELCIA_DIR
source venv/bin/activate
python delcia_web.py > log.txt 2>&1 &
deactivate
