#!/bin/bash
source venv/bin/activate
rm -R delcia_distrib
mkdir -p delcia_distrib
pip freeze > requirements.txt
cp -r  libs delcia_distrib/
cp -r  static delcia_distrib/
cp -r  templates delcia_distrib/
cp -r  delcia.py  delcia_distrib/
cp -r  delcia_toos.sh delcia_distrib/
cp -r  delcia_web.py delcia_distrib/
cp -r  requirements.txt delcia_distrib/
cp -r  licence.txt delcia_distrib/
cp -r  install.sh delcia_distrib/
cp -r  delcia_web_deamon.sh delcia_distrib/
cp -r  delcia_conf_distrib.json delcia_distrib/delcia_conf.json
tar -czvf delcia.tar.gz  --exclude='*__pycache__*' delcia_distrib
deactivate