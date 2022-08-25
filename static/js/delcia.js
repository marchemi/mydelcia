/*
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
*/
var last_data = {}
last_data.plugStatus == 0
last_data.chargingStatus == 0
last_data.level=0
last_data.autonomy=0
last_data.cron=0

var batterie_capacity = 27.4;
// Estimation Dacia 12 (7.5)
var batterie_perte = 7.5;


function loadData() {
  var currentURL = document.URL;
  state()
}

function state() {
    //alert(document.getElementById("button_onoff").disabled);
    var xhr = new XMLHttpRequest();
    var url = document.URL + "state"
    xhr.open("POST", url, true);
    xhr.responseType = 'json';
    xhr.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.onreadystatechange = function() {
    if (xhr.readyState === 4) {
        //alert(xhr.response); // Par défault une DOMString
        console.log(xhr.status);
        console.log(xhr.response);
        if  (xhr.status == 200) {
            upateState(xhr.response);
        }
      }
      document.getElementById("button_onoff").disabled = false;
    };
    xhr.send();
}



function onOff() {
    var onoff_value = (last_data.chargingStatus + 1) %2
    //alert(onoff_value)
    const data = new FormData();
    data.append("onoff", onoff_value);
    var xhr = new XMLHttpRequest();
    xhr.onreadystatechange = function() {
        console.log("onreadystatechange" + xhr.response)
        if (xhr.readyState === 4) {
            if (xhr.status >= 200) {
                //upateState(xhr.response)
                document.getElementById('chargingStatus').innerHTML = "...wait..."
                //console.log("onreadystatechange" + xhr.response)
                setTimeout(state, 20000)
            } else {
                alert("error" + xhr.response)
                var elt =  document.getElementById('button_onoff')
                document.getElementById("button_onoff").disabled = false;
            }
        }
    };
    var url = document.URL + "onoff"
    xhr.open("POST", url, true);
    xhr.responseType = 'json';
    xhr.send(data);
    document.getElementById("button_onoff").disabled = true;
}

function upateState(data) {
    last_data = data
    document.getElementById('level').innerHTML = data.level
    document.getElementById('autonomy').innerHTML = data.autonomy
    if (data.plugStatus == 0) {
        document.getElementById('plugStatus').innerHTML = "Débranché"
    } else {
        document.getElementById('plugStatus').innerHTML = "Branché"
    }
    if (data.chargingStatus == 0) {
        document.getElementById('chargingStatus').innerHTML = "Off"
    } else {
        document.getElementById('chargingStatus').innerHTML = "On"
    }
    document.getElementById('is_prog').innerHTML = data.cron
    refresh_estimated_charge_time(false)
}

function getAC() {
    var ele_power = document.getElementsByName('power');
    for(i = 0; i < ele_power.length; i++) {
        if(ele_power[i].checked) {
            ampere = ele_power[i].value
        }
    }
    return parseInt(ampere)
}

function getDuration() {
    var duration = 0
    var ele_time = document.getElementsByName('time');
    for(i = 0; i < ele_time.length; i++) {
        if(ele_time[i].checked) {
            duration = ele_time[i].value;
        }
    }
    return duration
}

function isMinuteCharge() {
     var ele_time = document.getElementById('min');
     return ele_time.checked
}

function getMinuteCharge() {
     user_min = document.getElementById('user_min').value
     tab_user_min = user_min.split(":")
     return parseInt(tab_user_min[0]) * 60 + parseInt(tab_user_min[1])
     //return parseInt(document.getElementById('user_min').value);
}

function getChargeStart() {
    var charge_start = 0
    var ele_time = document.getElementsByName('when');
    for(i = 0; i < ele_time.length; i++) {
        if(ele_time[i].checked) {
            charge_start = parseInt(ele_time[i].value);
        }
    }
    return charge_start
}

function getManualChargeDate() {
     return document.getElementById('user_date').value+":00";
}

function reset() {
    var xhr = new XMLHttpRequest();
    var url = document.URL + "reset"
    xhr.open("POST", url, true);
    xhr.responseType = 'json';
    xhr.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.onreadystatechange = function() {
    if (xhr.readyState === 4) {
        //alert(xhr.response); // Par défault une DOMString
        upateState(xhr.response)
      }
    document.getElementById('id_reset').disabled = false;
    };
    xhr.send();
    document.getElementById('id_reset').disabled = true;
}

function getCronTable() {
    if (last_data.cron == 0) {
        return
    }
    var xhr = new XMLHttpRequest();
    var url = document.URL + "crontable"
    xhr.open("POST", url, true);
    xhr.responseType = 'json';
    xhr.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.send();
    xhr.onreadystatechange = function() {
    if (xhr.readyState === 4) {
        //alert(xhr.response.crontable)
        //alert("toto")
        var popup = document.getElementById("myPopup");
        var res = xhr.response.crontable
        var crontable = ""
        res.forEach(function(ligne) {
             console.log(ligne);
             crontable+=ligne+"<br>";
        }
        );
        popup.innerHTML= crontable
        popup.classList.toggle("show");
        setTimeout(hidePopup, 4000)
      }
    };
}

function hidePopup() {
    console.log("hide popup")
    var popup = document.getElementById("myPopup");
    popup.classList.toggle("show");
}

function programCharge() {
        //alert("programCharge")
        var ac = getAC();
        var duration_batterie = 0;
        var duration_min = 0;
        var charge_start = getChargeStart();

        var charge_date = "" ;
        if (isMinuteCharge()) {
           //alert("duration_min ")
           duration_min = getMinuteCharge();
           //alert("duration_min " + duration_min)
        } else {
           //alert("duration_batterie ")
           duration_batterie = getDuration();
           //alert("duration_batterie " + duration_batterie)
        }


        if (charge_start == 2) {
            charge_date = getManualChargeDate()
        }
        const data = new FormData();
        data.append("ac", ac);
        data.append("duration_batterie", duration_batterie);
        data.append("duration_min", duration_min);
        data.append("charge_start", charge_start);
        data.append("charge_date", charge_date);
        data.append("level_batterie", parseInt(last_data.level))


        /*var data = {
            "ac": ac,
            "duration_batterie": duration_batterie,
            "duration_min" : duration_min,
            "charge_start" : charge_start,
            "charge_date" : charge_date
        }
        alert(JSON.stringify(data));
        */
        var xhr = new XMLHttpRequest();

        xhr.onreadystatechange = function() {
            console.log("onreadystatechange" + xhr.response)
            if (xhr.readyState === 4) {
                //alert(xhr.response); // Par défault une DOMString
                if (xhr.status >= 200) {
                    upateState(xhr.response)
                    console.log("onreadystatechange" + xhr.response)
                } else {
                    alert("error" + xhr.response)
                }
            }
            document.getElementById('id_prog').disabled = false;
        };
        var url = document.URL + "charge"
        xhr.open("POST", url, true);
        xhr.responseType = 'json';
        //xhr.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
        //xhr.setRequestHeader('Content-Type', 'application/json');
        //xhr.send(JSON.stringify(data));
        xhr.send(data);
        document.getElementById('id_prog').disabled = true;

        /*
        ac = int(request.form['ac'])
        duration_batterie = int(request.form['duration_batterie'])
        duration_min = int(request.form['duration_min'])
        charge_start = int(request.form['charge_start'])
        charge_date = request.form['charge_date']
        */
}

function refresh_estimated_charge_time(refresh_user_min) {
  baterrie = document.getElementById('level').innerHTML;
  var ele_power = document.getElementsByName('power');
  for(i = 0; i < ele_power.length; i++) {
    if(ele_power[i].checked) {
        ampere = ele_power[i].value
    }
  }
  switch (ampere) {
  case '32':
    kwh = 6.6
    break;
  case '16':
    kwh = 3.68
    break;
  case '10':
    kwh = 2.3
    break;
  case '8':
    kwh = 1.84
    break;
  default:
    console.log('Error');
  }
  res_80 = get_charging_time(kwh, baterrie, 80)
  res_100 = get_charging_time(kwh, baterrie, 100)
  ele_label_80 = document.getElementById('minto80');
  ele_label_100 = document.getElementById('minto100');
  str_heure_80 = getIn_heure(res_80)
  str_heure_100 = getIn_heure(res_100)
  str_min_80 = getIn_minute(res_80)
  str_min_100 = getIn_minute(res_100)

  ele_label_80.innerHTML = str_heure_80 + "h "+str_min_80 + "m"
  ele_label_100.innerHTML = str_heure_100 + "h "+ str_min_100 + "m"

  if (!refresh_user_min) {
    return
  }
  user_min = document.getElementById('user_min');
  if (str_heure_80 < 10) {
    str_heure_80 =  "0"+str_heure_80;
  }
  if (str_heure_100.length < 10) {
    str_heure_100 =  "0"+str_heure_100;
  }
  if (str_min_80 < 10) {
    str_min_80 =  "0"+str_min_80;
  }
  if (str_min_100 < 10) {
    str_min_100 =  "0"+str_min_100;
  }
  //console.log(str_heure_80 + ":" +str_min_80 + ":00")
  user_min.value = str_heure_80 + ":" +str_min_80 + ":00";
}

function getIn_heure(time) {
    return Math.trunc(time)
}
function getIn_minute(time){
    h = Math.trunc(time)
    return Math.round((time - h) * 60)
}


function get_charging_time(kwh, batterie_level, reach_batterie) {
    var time_80 = ((batterie_capacity * 80)/100)/kwh;
    time_80  = time_80 + ((time_80 * batterie_perte)/100)
    var time_100 = time_80 + ((time_80*50)/100);
/*
    if (kwh == 7.36){
        time_80 = 3.70
        time_100 = 4.83
    } else if (kwh == 3.68){
        time_80 = 6.67
        time_100 = 8.32
    } else if  (kwh == 2.3){
        time_80 = 11.42
        time_100 = 13.45
    } else if (kwh == 1.84) {
        time_80 = 13.77
        time_100 = 20
    }
*/
    var charge_dacia_80 = 0
    if (batterie_level < 80) {
       charge_dacia_80 = ((reach_batterie - batterie_level) * time_80)/ 80
       //charge_dacia_80  = charge_dacia_80 + ((charge_dacia_80 * batterie_perte)/100)
    }
    charge_dacia_100 = ((reach_batterie - batterie_level) * time_100)/ 100
    //charge_dacia_100 = charge_dacia_100 + ((charge_dacia_100 * batterie_perte)/100)
     if (reach_batterie == 80)
        return charge_dacia_80
    else
        return charge_dacia_100
}

