"""
MIT License
Copyright (c) 2022, Mikael Marche

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
import os
import sys
import datetime
import time
import json

login = None
def load_conf():
    # Opening JSON file
    f = open('delcia_conf.json')
    config = json.load(f)
    f.close()
    print(config)
    return config

conf = load_conf()

login = conf['DACIA_LOGIN']
password = conf['DACIA_PASSWORD']
account_id = conf['DACIA_ACCOUNT']
VIN = conf['DACIA_VIN']
CRONFILE = conf['CRONFILE']
if (CRONFILE == ''):
    CRONFILE=None
PORT = conf['PORT']
DEBUG = conf['DEBUG']
currentUser = conf['USER']
if (currentUser == ''):
    currentUser = os.getlogin()

add_user_to_cmd = conf['ADD_USER_TO_CRON']

def get_heure_creuse_midi(now):
    now1 = time.gmtime().tm_hour
    now2 = time.localtime().tm_hour
    decalage_horraire = datetime.timedelta(hours=now2 - now1)
    heure_creuse = datetime.datetime(now.year, now.month, now.day, 12, 38, 0) + decalage_horraire
    return heure_creuse , heure_creuse + datetime.timedelta(hours=2)

def get_heure_creuse_soir(now):
    now1 = time.gmtime().tm_hour
    now2 = time.localtime().tm_hour
    decalage_horraire = datetime.timedelta(hours=now2 - now1)
    heure_creuse = datetime.datetime(now.year, now.month, now.day, 1, 38, 0) + decalage_horraire
    return heure_creuse , heure_creuse + datetime.timedelta(hours=5)


def get_script_path():
    return os.path.dirname(os.path.realpath(sys.argv[0]))
