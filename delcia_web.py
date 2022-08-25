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
from flask import Flask, render_template, jsonify, request, Response

import libs.delcia_api
import libs.delcia_api as delcia
import asyncio
import datetime

app = Flask('delcia', static_folder='static')
loop = asyncio.get_event_loop()


@app.route('/', methods=["GET"])
def index():
    return render_template("index.html")


@app.route('/state', methods=["POST"])
def state():
    try:
        data_response = {}
        loop.run_until_complete(delcia.get_vehicule_state(data_response))
        delcia.add_cron_state(data_response)
        print(data_response)
        return jsonify(data_response)
    except Exception as e:
        return Response(f"Error {str(e)}", status=400)


@app.route('/onoff', methods=["POST"])
def onoff():
    try:
        data_response = {}
        value = int(request.form['onoff'])
        if value == 0 or value == 1:
            loop.run_until_complete(delcia.set_vehicule_charge(value, data_response))
            delcia.add_cron_state(data_response)
            return jsonify(data_response)
        else:
            return Response("Error : value must be 0 or 1", status=400)
    except Exception as e:
        return Response(f"Error {str(e)}", status=400)


@app.route('/charge', methods=["POST"])
def charge():
    try:
        data_response = {}
        error = "Error in parameters format"
        date = None
        print(request.form)
        ac = int(request.form['ac'])
        duration_batterie = int(request.form['duration_batterie'])
        duration_min = int(request.form['duration_min'])
        charge_start = int(request.form['charge_start'])
        charge_date = request.form['charge_date']
        level_batterie = int(request.form['level_batterie'])

        error = "Unkown Error"

        if ac not in [8, 10, 16, 32]:
            return Response("Error parameter ac", status=400)

        if duration_batterie not in [0, 80, 100]:
            return Response("Error parameter duration_batterie ", status=400)

        if duration_min < 0:
            return Response("Error parameter duration_min", status=400)

        if duration_min == 0 and duration_batterie == 0:
            return Response("Error parameter charge_start ", status=400)

        if charge_date == "" and charge_start not in [0, 1]:
            return Response("Error parameter charge_date ", status=400)

        if charge_date != "" and charge_start not in [0, 1]:
            error = "Error format in charge_date"
            charge_date = datetime.date.today().strftime("%d/%m/%Y") + " " + charge_date
            date = datetime.datetime.strptime(charge_date, "%d/%m/%Y %H:%M:%S")
            error = "Unkown Error"

        loop.run_until_complete(
            delcia.set_charge(ac, duration_batterie, duration_min, charge_start, date, level_batterie, data_response))
        delcia.add_cron_state(data_response)
        return jsonify(data_response)
    except Exception as e:
        print(error)
        return Response(f"{error} : {str(e)}", status=400)


@app.route('/crontable', methods=["POST"])
def crontable():
    try:
        data_response = {}
        data_response["crontable"] = delcia.get_cron_table()
        return jsonify(data_response)
    except Exception as e:
        print(f"Error {str(e)}")
        return Response(f"Error {str(e)}", status=400)


@app.route('/reset', methods=["POST"])
def reset():
    try:
        data_response = {}
        loop.run_until_complete(delcia.reset(data_response))
        delcia.add_cron_state(data_response)
        return jsonify(data_response)
    except Exception as e:
        return Response(f"Error {str(e)}", status=400)

if (libs.delcia_api.conf.DEBUG):
    #app.run(debug=True, port=libs.delcia_api.conf.PORT)
    app.run(host='0.0.0.0', port=libs.delcia_api.conf.PORT, debug=False)
else:
    app.run(host='0.0.0.0', port=libs.delcia_api.conf.PORT, debug=False)
