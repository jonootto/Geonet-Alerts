import requests
import json
from dateutil.parser import parse
from datetime import datetime, timezone
import time
from geopy import distance
from colorama import Fore, Style
import meshtastic
import meshtastic.tcp_interface
from pubsub import pub
import time
import os
from dotenv import load_dotenv


load_dotenv()
api = "https://api.geonet.org.nz/quake?MMI=-1"
maxdist = 400 #km
radioHostname = os.environ["RADIO_HOSTNAME"]
channel = int(os.environ.get("CHANNEL_INDEX",1))


def onConnection(interface, topic=pub.AUTO_TOPIC):
    print("Connected to radio: " + interface.getLongName())

def dstWlg(pos):
    wellington = (-41.32, 174.81)
    return round(distance.distance(wellington, pos).km)

def getPos(coordinates):
    lat = coordinates[1]
    lon = coordinates[0]
    pos = (lat, lon)
    return (pos)


def getQuakes():
    r = requests.get(api,headers={"Accept": "application/vnd.geo+json;version=2"})
    if r.status_code == 200:
        return r.json()
    else:
        print("Error:" + str(r.status_code))
    

def utc_to_local(utc_dt):
    return utc_dt.replace(tzinfo=timezone.utc).astimezone(tz=None)

def readSaved():
    f = open("last.txt", "r")
    return json.load(f)

def getDelay(lasttime):
        timenow = datetime.now().replace(tzinfo=None)
        lasttime = lasttime.replace(tzinfo=None)
        timediff = (timenow - lasttime).total_seconds()
        return round(timediff)

def saveLast(timestamp,id):
    data = {
        "timestamp" : str(timestamp),
        "id" : str(id)
    }
    with open('last.txt', 'w') as f:
        json.dump(data, f, ensure_ascii=False)
    return

def connectMeshtastic(host):
    while True:
        try:
            print("Connecting to radio...")
            radio = meshtastic.tcp_interface.TCPInterface(hostname=host)
            break
        except Exception as e: 
            print(e)
            print(Fore.RED + "Connection Failed" + Style.RESET_ALL)
    return radio

lastQuakes = ""
savedEvent = readSaved()
savedTime = parse(savedEvent["timestamp"]).replace(tzinfo=None)
print("Last event "+ savedEvent["id"] +" at " + savedTime.strftime("%r %A %d %B %y"))

pub.subscribe(onConnection, "meshtastic.connection.established")
interface = connectMeshtastic(radioHostname)
print("Connect test successful")
interface.close()

while True:
    quakes = getQuakes()
    if quakes != lastQuakes:
        lastQuakes = quakes
        print("New Data")
        if quakes:
            lastevent = quakes['features'][0]
            lasttime = utc_to_local(parse(lastevent['properties']['time']))
            lastid = str(lastevent['properties']['publicID'])
            saveid = readSaved()["id"]

            #New Quake
            if saveid != lastid:
                lastpos = getPos(lastevent['geometry']['coordinates'])
                locname = lastevent['properties']['locality']
                mag = str(round(lastevent['properties']['magnitude'],1))
                dist = dstWlg(lastpos)
                if dist < maxdist:
                    msg = str("New Quake at " +lasttime.strftime("%r %A %d %B %y")+ ". Magnitude: " + mag + ". " + str(dist) + "km from Wellington, " + locname)
                    print(msg)
                    interface = connectMeshtastic(radioHostname)
                    print("Sending to mesh...")
                    interface.sendText(msg,channelIndex=channel,wantAck=True)
                    interface.close()
                    print("Time now " + datetime.now().strftime("%r %A %d %B %y") + " Reporting delay: " + str(getDelay(lasttime)) + " seconds")
                else:
                    print("Quake " + str(dist) + "km away, " + locname)
                saveLast(lasttime,lastid)

        else:
            print(Fore.RED + "Error Retreiving Quakes" + Style.RESET_ALL)
    time.sleep(5)

interface.close()