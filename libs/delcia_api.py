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
import aiohttp
import datetime
import libs.user_conf as conf
from crontab import CronTab

from renault_api.renault_client import RenaultClient

login = conf.login
password = conf.password
account_id = conf.account_id
VIN = conf.VIN
DELCIA_DIR = conf.get_script_path()
currentUser = conf.currentUser

CRON_COMMENT = "Delcia API"
prefix_cmd=""
if conf.add_user_to_cmd:
    prefix_cmd = currentUser + " "

batterie_capacity = 27.4
#Estimation Dacia 12 (7.5)
batterie_perte = 7.5

CRON_CMD_STOP = prefix_cmd + DELCIA_DIR + "/delcia_toos.sh -stop"
CRON_CMD_START = prefix_cmd + DELCIA_DIR + "/delcia_toos.sh -start"
CRON_CMD_INIT = prefix_cmd + DELCIA_DIR + "/delcia_toos.sh -init"
DEBUG = conf.DEBUG

def _get_cron_table():
    if DEBUG:
        system_cron = CronTab(tabfile='crontab', user=False)
    else:
        if conf.CRONFILE is not None:
            system_cron = CronTab(tabfile=conf.CRONFILE, user=currentUser)
        else:
            system_cron = CronTab(user=currentUser)
    return system_cron

async def _get_websession(websession, login, password):
    if DEBUG:
        return
    client = RenaultClient(websession=websession, locale="fr_FR")
    await client.session.login(login, password)
    return client


async def _get_batterie_level(data):
    print(f"_get_batterie_level {DEBUG}")
    if DEBUG:
        print("_get_batterie_level")
        return 63
    await get_vehicule_state(data)


def _set_details_vehicule(data, details):
    data["level"] = details.batteryLevel
    data["autonomy"] = details.batteryAutonomy

    # UNPLUGGED = 0
    # PLUGGED = 1
    # PLUG_ERROR = -1
    # PLUG_UNKNOWN = -2147483648
    if (details.plugStatus != 1) and (details.plugStatus != 1):
        data["plugStatus"] = 0
    else:
        data["plugStatus"] = details.plugStatus

    # NOT_IN_CHARGE = 0.0
    # WAITING_FOR_A_PLANNED_CHARGE = 0.1
    # CHARGE_ENDED = 0.2
    # WAITING_FOR_CURRENT_CHARGE = 0.3
    # ENERGY_FLAP_OPENED = 0.4
    # CHARGE_IN_PROGRESS = 1.0
    ## This next is more accurately "not charging" (<= ZE40) or "error" (ZE50).
    # CHARGE_ERROR = -1.0
    # UNAVAILABLE = -1.1

    if (details.chargingStatus < 0) or ((details.chargingStatus > 0) and (details.chargingStatus < 1)):
        data["chargingStatus"] = 0.0
    else:
        data["chargingStatus"] = details.chargingStatus


def _get_charging_time_theo(kwh, batterie_level, reach_batterie):
    time_80 = ((batterie_capacity * 80) / 100) / kwh
    time_80 = time_80 + ((time_80 * batterie_perte) / 100)
    time_100 = time_80 + ((time_80 * 50) / 100)
    #if kwh == 7.36:
    #    time_80 = 3.70
    #    time_100 = 4.83
    #elif kwh == 3.68:
    #    time_80 = 6.67
    #    time_100 = 8.32
    #elif kwh == 2.3:
    #    time_80 = 11.42
    #    time_100 = 13.45
    #elif kwh == 1.84:
    #    time_80 = 13.77
    #    time_100 = 20
    charge_dacia_80 = 0
    if batterie_level < 80:
        charge_dacia_80 = ((reach_batterie - batterie_level) * time_80) / 80
    charge_dacia_100 = ((reach_batterie - batterie_level) * time_100) / 100
    return charge_dacia_80, charge_dacia_100


def _get_charging_time_theo2(kwh, batterie_level):
    kwatt_to_charge = batterie_capacity - ((batterie_level * batterie_capacity) / 100)
    charge_theo_80 = 0
    if batterie_level < 80:
        charge_theo_80 = ((kwatt_to_charge) * 80 / 100) / kwh
        charge_theo_100 = (charge_theo_80 * 50 / 100) + charge_theo_80
    else:
        charge_theo_100 = ((kwatt_to_charge)) / kwh

    return charge_theo_80, charge_theo_100


def _getIn_h_m(time):
    h = int(time)
    m = int(round((time - h) * 60))
    print(f"Estimation de temps de charhe : {h}h:{m}m")
    return h, m


def _exec_script(program):
    exec(program)


def _get_cron_entry_charge_instantaly(time_to_charge):
    cron_entry = []
    h, m = _getIn_h_m(time_to_charge)
    # Initialisation des parametres
    time_charge = datetime.timedelta(hours=h, minutes=m)
    # time_charge = datetime.timedelta(hours=12, minutes=1)
    now = datetime.datetime.now()
    # now = datetime.datetime.now() + datetime.timedelta(hours=12)
    new_time = now + time_charge
    print(f"Date de fin de charge  : {new_time} si départ maintenant {now}")

    cron_entry.append((CRON_CMD_START, datetime.datetime.now() + datetime.timedelta(minutes=1)))
    cron_entry.append((CRON_CMD_STOP, new_time))
    cron_entry.append((CRON_CMD_INIT, new_time + datetime.timedelta(minutes=2)))
    return cron_entry


def _get_cron_entry_charge_at(time_to_charge, date):
    cron_entry = []
    h, m = _getIn_h_m(time_to_charge)
    # Initialisation des parametres
    time_charge = datetime.timedelta(hours=h, minutes=m)
    # now = datetime.datetime.now() + datetime.timedelta(hours=12)
    new_time = date + time_charge
    print(f"Date de fin de charge  : {new_time} si départ à {date}")

    cron_entry.append((CRON_CMD_START, date + datetime.timedelta(minutes=1)))
    cron_entry.append((CRON_CMD_STOP, new_time))
    cron_entry.append((CRON_CMD_INIT, new_time + datetime.timedelta(minutes=2)))
    return cron_entry


def _get_cron_entry_charge_delay2(time_to_charge):
    cron_entry = []
    h, m = _getIn_h_m(time_to_charge)
    # Initialisation des parametres
    time_charge = datetime.timedelta(hours=h, minutes=m)
    # time_charge = datetime.timedelta(hours=12, minutes=1)
    now = datetime.datetime.now()
    # now = datetime.datetime.now() + datetime.timedelta(hours=12)
    new_time = now + time_charge
    print(f"Date de fin de charge  : {new_time} si départ maintenant {now}")

    # date des prochaine heures creuse
    heure_creuse_midi_begin, heure_creuse_midi_end = conf.get_heure_creuse_midi(now)
    heure_creuse_nuit_begin, heure_creuse_nuit_end = conf.get_heure_creuse_soir(now)

    decalage_jour = False
    decalage_nuit = False

    if now > heure_creuse_midi_end:
        heure_creuse_midi_begin = heure_creuse_midi_begin + datetime.timedelta(days=1)
        heure_creuse_midi_end = heure_creuse_midi_end + datetime.timedelta(days=1)
        decalage_jour = True


    if now > heure_creuse_nuit_end:
        heure_creuse_nuit_begin = heure_creuse_nuit_begin + datetime.timedelta(days=1)
        heure_creuse_nuit_end = heure_creuse_nuit_end + datetime.timedelta(days=1)
        decalage_nuit = True

    print(f"Heure creuse midi  = {heure_creuse_midi_begin} to {heure_creuse_midi_end}")
    print(f"Heure creuse soir  = {heure_creuse_nuit_begin} to {heure_creuse_nuit_end}")

    date_charche = now + datetime.timedelta(minutes=2)
    # calcul des prochaines heures creuses
    debut = 1  # 0 = now, 1 = midi, 2 = nuit
    if (heure_creuse_midi_begin < now) and (now < heure_creuse_midi_end):
        # On est dans les heures creuses du midi
        print('On est dans les heures creuses du midi')
        debut = 1
    elif (heure_creuse_nuit_begin < now) and (now < heure_creuse_nuit_end):
        # On est dans les heures creuses du soir
        print('On est dans les heures creuses du soir')
        debut = 2
    elif (now < heure_creuse_midi_begin) and (decalage_jour == False):
        # on est le matin apres les heure creuse de la nuit et avant le midi
        print('on est le matin apres les heure creuse de la nuit et avant le midi')
        debut = 1
        date_charche = heure_creuse_midi_begin
    else:
        # on est apres les heures creuse du midi et avant la nuit
        print('on est apres les heures creuse du midi et avant la nuit')
        debut = 2
        date_charche = heure_creuse_nuit_begin

    print(f"prochaine date de charge = {date_charche}")
    end_date_charche = date_charche + time_charge
    print(f"End charging Time = {end_date_charche}")

    print(f"{CRON_CMD_START} à {date_charche}")
    cron_entry.append((CRON_CMD_STOP, datetime.datetime.now() + datetime.timedelta(minutes=1)))
    cron_entry.append((CRON_CMD_START, date_charche))

    if (debut == 1) and (end_date_charche > heure_creuse_midi_end):
        delta = heure_creuse_midi_end - date_charche
        time_charge = time_charge - delta
        end_date_charche = heure_creuse_nuit_begin + time_charge
        print(f"Besoin de continuer la charge la nuit pour {time_charge} jusqu'a {end_date_charche} h")
        print(f"Fin charge à {heure_creuse_midi_end}")
        cron_entry.append((CRON_CMD_STOP, heure_creuse_midi_end))

        print(f"Début charge à {heure_creuse_nuit_begin}")
        cron_entry.append((CRON_CMD_START, heure_creuse_nuit_begin))

        print(f"Fin charge à {end_date_charche}")
        cron_entry.append((CRON_CMD_STOP, end_date_charche))

    elif (debut == 2) and (end_date_charche > heure_creuse_nuit_end):
        print(f"Besoin de continuer la charge le jour")
        delta = heure_creuse_nuit_end - date_charche
        time_charge = time_charge - delta
        end_date_charche = heure_creuse_midi_begin + time_charge
        print(f"Besoin de continuer la charge le jour pour {time_charge} jusqu'a {end_date_charche} h")

        print(f"Fin charge à {heure_creuse_nuit_end}")
        cron_entry.append((CRON_CMD_STOP, heure_creuse_nuit_end))

        print(f"Début charge à {heure_creuse_midi_begin}")
        cron_entry.append((CRON_CMD_START, heure_creuse_midi_begin))

        print(f"Fin charge à {end_date_charche}")
        cron_entry.append((CRON_CMD_STOP, end_date_charche))
    else:
        print(f"Fin charge à {end_date_charche}")
        cron_entry.append((CRON_CMD_STOP, end_date_charche))

    print(f"Script Delete all entries")
    cron_entry.append((CRON_CMD_INIT, end_date_charche + datetime.timedelta(minutes=2)))
    return cron_entry


def _get_cron_entry_charge_delay(time_to_charge):
    cron_entry = []
    h, m = _getIn_h_m(time_to_charge)
    # Initialisation des parametres
    time_charge = datetime.timedelta(hours=h, minutes=m)
    # time_charge = datetime.timedelta(hours=12, minutes=1)
    now = datetime.datetime.now()
    # now = datetime.datetime.now() + datetime.timedelta(hours=12)
    new_time = now + time_charge
    print(f"Date de fin de charge  : {new_time} si départ maintenant {now}")

    # date des  heures creuse
    heure_creuse_midi_begin, heure_creuse_midi_end = conf.get_heure_creuse_midi(now)
    heure_creuse_nuit_begin, heure_creuse_nuit_end = conf.get_heure_creuse_soir(now)

    decalage = 2
    reste_a_charger = True
    cron_entry.append((CRON_CMD_STOP, datetime.datetime.now() + datetime.timedelta(minutes=1)))
    while reste_a_charger:
        debut = 0
        date_charche = now + datetime.timedelta(minutes=decalage)
        now = date_charche
        #On est dans les heures creuse ?
        if (heure_creuse_midi_begin <= now) and (now < heure_creuse_midi_end):
            # On est dans les heures creuses du midi
            print('On est dans les heures creuses du midi')
            debut = 1
            #date_charche = now + datetime.timedelta(minutes=2)
        elif (heure_creuse_nuit_begin <= now) and (now < heure_creuse_nuit_end):
            # On est dans les heures creuses du soir
            print('On est dans les heures creuses de nuit')
            debut = 2
            #date_charche = now + datetime.timedelta(minutes=2)
        elif now < heure_creuse_nuit_begin:
            print('On est avant les heures creuses de nuit')
            debut = 2
            date_charche = heure_creuse_nuit_begin
        elif now < heure_creuse_midi_begin:
            print('On est apres les heurs creuse de nuit et avant les heures creuses de midi ')
            date_charche = heure_creuse_midi_begin
            debut = 1
        else :
            # on est apres les heures creuse du jours, il faut decaler
            debut = 3

        end_date_charche = date_charche + time_charge
        if debut == 1:
            decalage = 0
            #On commence à charger pendant les heures creuses du midi
            print(f"On commence à charger pendant les heures creuses du midi")
            print(f"Debut charge à {date_charche}")
            cron_entry.append((CRON_CMD_START, date_charche))
            if end_date_charche > heure_creuse_midi_end:
                #Calcul du nouveau time_charge
                print(f"Calcul du reste a charger")
                delta = heure_creuse_midi_end - date_charche
                time_charge = time_charge - delta
                print(f"Fin charge à {heure_creuse_midi_end}")
                print(f"Restera a charger : {time_charge}")
                cron_entry.append((CRON_CMD_STOP, heure_creuse_midi_end))
                # La nouvelle recharge possible est le jour suivant
                debut = 3
            else:
                print(f"Pas de reste à charger")
                print(f"Fin charge à {end_date_charche}")
                cron_entry.append((CRON_CMD_STOP, end_date_charche))
                reste_a_charger = False

        elif debut == 2:
            decalage = 0
            #On commence à charger pendant les heures creuses de nuit
            print(f"On commence à charger pendant les heures creuses de nuit")
            print(f"Debut charge à {date_charche}")
            cron_entry.append((CRON_CMD_START, date_charche))
            if end_date_charche > heure_creuse_nuit_end:
                # Calcul du nouveau time_charge
                delta = heure_creuse_nuit_end - date_charche
                time_charge = time_charge - delta
                print(f"Fin charge à {heure_creuse_nuit_end}")
                print(f"Restera a charger : {time_charge}")
                cron_entry.append((CRON_CMD_STOP, heure_creuse_nuit_end))
                # La nouvelle recharge possible est les heures creuse de midi
                now = heure_creuse_midi_begin
            else:
                print(f"Fin charge à {end_date_charche}")
                cron_entry.append((CRON_CMD_STOP, end_date_charche))
                print(f"pPas de reste à charger")
                reste_a_charger = False

        if debut == 3:
            # On decalle le prochain début au jour suivant
            print('La nouvelle recharge possible est le jour suivant, On decalle')
            heure_creuse_midi_begin = heure_creuse_midi_begin + datetime.timedelta(days=1)
            heure_creuse_midi_end = heure_creuse_midi_end + datetime.timedelta(days=1)
            heure_creuse_nuit_begin = heure_creuse_nuit_begin + datetime.timedelta(days=1)
            heure_creuse_nuit_end = heure_creuse_nuit_end + datetime.timedelta(days=1)
            now = heure_creuse_nuit_begin

    print(f"Script Delete all entries")
    cron_entry.append((CRON_CMD_INIT, end_date_charche + datetime.timedelta(minutes=2)))
    return cron_entry


def _init_cron_table():
    cron = _get_cron_table()
    cron.remove_all(comment=CRON_COMMENT)
    cron.write()


def _writre_cron_table(cron_entry):
    cron = _get_cron_table()
    for commande, date in cron_entry:
        print(f"Command : {commande}, at {date}")
        now = datetime.datetime.now()
        job = cron.new(command=commande, user=currentUser, comment=CRON_COMMENT)
        job.minutes.on(date.minute)
        job.day.on(date.day)
        job.hour.on(date.hour)
        job.month.on(date.month)
    cron.write()
    #system_cron.write_to_user(user=currentUser)


# Public API

def _get_debug_sate(data, level=40, autonomy=168, plugStatus=0, chargingStatus=0.0):
    data["level"] = level
    data["autonomy"] = autonomy
    data["plugStatus"] = plugStatus
    data["chargingStatus"] = chargingStatus


async def get_vehicule_state(data):
    if DEBUG:
        _get_debug_sate(data)
    else:
        async with aiohttp.ClientSession() as renault_session:
            client = RenaultClient(websession=renault_session, locale="fr_FR")
            await client.session.login(login, password)
            account = await client.get_api_account(account_id)
            vehicle = await account.get_api_vehicle(VIN)
            details = await vehicle.get_battery_status()
            _set_details_vehicule(data, details)
    return data


def _get_cron_state():
    cron = _get_cron_table()
    iter = cron.find_comment(CRON_COMMENT)
    for job in iter:
        return 1
    return 0


def add_cron_state(data):
    data["cron"] = _get_cron_state()


def get_cron_table():
    cron = _get_cron_table()
    iter = cron.find_comment(CRON_COMMENT)
    line = 0
    res = []
    for job in iter:
        line = line + 1
        add = True
        command = job.command
        if command != CRON_CMD_INIT:
            str_cmd = "Debut"
            if command == CRON_CMD_STOP:
                str_cmd = "Fin"
                if line == 1:
                    add = False
            entry = f"{str_cmd} à {job.day}/{job.month}, {job.hour}h:{job.minutes}m"
            print(entry)
            if add:
                res.append(entry)
    return res


async def set_vehicule_charge(onOff, data):
    if DEBUG:
        _get_debug_sate(data, level=76, autonomy=168, plugStatus=1, chargingStatus=1.0)
        return
    async with aiohttp.ClientSession() as renault_session:
        client = RenaultClient(websession=renault_session, locale="fr_FR")
        await client.session.login(login, password)
        account = await client.get_api_account(account_id)
        vehicle = await account.get_api_vehicle(VIN)
        details = await vehicle.get_battery_status()
        _set_details_vehicule(data, details)
        if data["plugStatus"] == 0:
            return
        if onOff == 0 and data["chargingStatus"] == 1.0:
            await vehicle.set_charge_stop()
        elif onOff == 1 and data["chargingStatus"] == 0.0:
            await vehicle.set_charge_start()
        else:
            return
        details = await vehicle.get_battery_status()
        _set_details_vehicule(data, details)


async def set_charge(ac_power, reach_batterie, duration_min, charge_start, charge_date, batterie_level, data):
    stop_charge = True
    ac_kw = 3.7
    if ac_power == 32:
        ac_kw = 6.6
    elif ac_power == 16:
        ac_kw = 3.68
    elif ac_power == 10:
        ac_kw = 2.3
    elif ac_power == 8:
        ac_kw = 1.84
    theo_80, theo_100 = _get_charging_time_theo(ac_kw, batterie_level, reach_batterie)
    if (reach_batterie == 80):
        duration = theo_80
    elif (reach_batterie == 100):
        duration = theo_100
    else:
        duration = (duration_min + 1) / 60
    cron_entry = None
    if (charge_start == 0):
        cron_entry = _get_cron_entry_charge_instantaly(duration)
        stop_charge = False
    elif (charge_start == 1):
        cron_entry = _get_cron_entry_charge_delay(duration)
    elif (charge_date != None):
        cron_entry = _get_cron_entry_charge_at(duration, charge_date)
    if cron_entry is not None:
        if stop_charge:
            if DEBUG:
                _get_debug_sate(data, level=73, autonomy=168, plugStatus=1, chargingStatus=0.0)
            else:
                await set_vehicule_charge(0, data)
        else:
            if DEBUG:
                _get_debug_sate(data, level=74, autonomy=169, plugStatus=1, chargingStatus=1.0)
            else:
                await  set_vehicule_charge(1, data)
        _init_cron_table()
        _writre_cron_table(cron_entry)


async def reset(data):
    _init_cron_table()
    await set_vehicule_charge(0, data)
