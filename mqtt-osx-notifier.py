#!/usr/bin/env python

# Copyright (C) 2013, Jan-Piet Mens <jpmens()gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.

import mosquitto
import socket
import sys, time
from ConfigParser import SafeConfigParser
from pync import Notifier   # https://github.com/SeTem/pync
import os

def config(inifile):
    cf = SafeConfigParser()
    cf.read(inifile)

    return cf

def on_connect(mosq, userdata, rc):
    print "Connected"
    for topic in userdata['topics']:
        print "Subscribing to " + topic
        mqttc.subscribe(topic, 2)

def on_message(mosq, userdata, msg):
    print(msg.topic+" "+str(msg.qos)+" "+str(msg.payload))

    cf = userdata['cf']
    application = cf.get('notifier', 'application')

    s = str(msg.topic) + "\n" + str(msg.payload)

    Notifier.notify(s,  title=application)

def on_subscribe(mosq, userdata, mid, granted_qos):
    pass

def on_disconnect(mosq, userdata, rc):
    print "OOOOPS! disconnect"
    time.sleep(10)


cf = config('mqtt-osx-notifier.ini')

topics = []
for key, topic in cf.items('topics'):
    topics.append(topic)

userdata = {
    'cf' : cf,
    'topics' : topics,
}

clientid = 'mqtt-osx-notifier-%s' % os.getpid()
mqttc = mosquitto.Mosquitto(clientid, userdata=userdata, clean_session=False)
mqttc.on_message = on_message
mqttc.on_connect = on_connect
mqttc.on_disconnect = on_disconnect
mqttc.on_subscribe = on_subscribe

mqttc.will_set('clients/mqtt-osx-notifier', payload="Adios!", qos=0, retain=False)

# Delays will be: 3, 6, 12, 24, 30, 30, ...
mqttc.reconnect_delay_set(delay=3, delay_max=30, exponential_backoff=True)

mqttc.connect(cf.get('mqtt', 'broker'), cf.getint('mqtt', 'port'), 60)

while True:
    try:
        mqttc.loop_forever()
    except socket.error:
        time.sleep(5)
    except KeyboardInterrupt:
        sys.exit(0)

