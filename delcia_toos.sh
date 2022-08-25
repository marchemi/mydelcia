#!/bin/bash
if [[ -z "${DELCIA_DIR}" ]]; then
  DELCIA_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
fi
#sudo nohup python app1c.py > log.txt 2>&1 &
#echo $DELCIA_DIR
cd $DELCIA_DIR
source venv/bin/activate
python delcia.py $1
deactivate
