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
minmag = 2
radioHostname = os.environ["RADIO_HOSTNAME"]
channel = int(os.environ.get("CHANNEL_INDEX",1))

timef = "%r %A %d %B %y"

def onConnection(interface, topic=pub.AUTO_TOPIC):
    #print notification when connection succeeds
    print("Connected to radio: " + interface.getLongName())

def dstWlg(pos):
    #Calculate distance of a positon from wellingotn airport
    #todo: make this work with user specified location
    wellington = (-41.32, 174.81)
    return round(distance.distance(wellington, pos).km)

def getPos(coordinates):
    #convert positon json into tuple
    lat = coordinates[1]
    lon = coordinates[0]
    pos = (lat, lon)
    return (pos)


def getQuakes():
    #Pull from geonet api
    r = requests.get(api,headers={"Accept": "application/vnd.geo+json;version=2"})
    if r.status_code == 200:
        return r.json()
    else:
        print("Error:" + str(r.status_code))
    

def utc_to_local(utc_dt):
    #convert time into local time
    return utc_dt.replace(tzinfo=timezone.utc).astimezone(tz=None)

def readSaved():
    #load last saved event from disk
    f = open("last.txt", "r")
    output  = json.load(f)
    f.close()
    return output

def getDelay(lasttime):
        #calculate how long between quake and now (mostly delay from api having info)
        timenow = datetime.now().replace(tzinfo=None)
        lasttime = lasttime.replace(tzinfo=None)
        timediff = (timenow - lasttime).total_seconds()
        return round(timediff)

def saveLast(timestamp,id):
    #store event to disk so its not resent if script restarted
    data = {
        "timestamp" : str(timestamp),
        "id" : str(id)
    }
    with open('last.txt', 'w') as f:
        json.dump(data, f, ensure_ascii=False)
        f.close()
    return

def connectMeshtastic(host):
    #connect to meshtastic radio
    while True:
        try:
            print("Connecting to radio...")
            radio = meshtastic.tcp_interface.TCPInterface(hostname=host)
            return radio
        except Exception as e: 
            print(e)
            print(Fore.RED + "Connection Failed" + Style.RESET_ALL)
        time.sleep(0.1)

def sendMsg(msgtxt):
    #send message over spefified channel
    intf = connectMeshtastic(radioHostname)
    time.sleep(0.5)
    print("Sending to mesh...")
    intf.sendText(msgtxt,channelIndex=channel,wantAck=True,)
    print("message sent")
    time.sleep(1)
    intf.close()

def connectTest():
    intf = connectMeshtastic(radioHostname)
    print("Connect test successful")
    intf.close()

lastQuakes = ""
savedEvent = readSaved()
savedTime = parse(savedEvent["timestamp"]).replace(tzinfo=None)
print("Last event "+ savedEvent["id"] +" at " + savedTime.strftime(timef))


pub.subscribe(onConnection, "meshtastic.connection.established")
#connectTest()

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
                if (dist < maxdist) and (float(mag) >= float(minmag)):
                    msg = str("New Quake at " +lasttime.strftime(timef)+ ". Magnitude: " + mag + ". " + str(dist) + "km from Wellington, " + locname)
                    print(msg)
                    sendMsg(msg)
                    print("Time now " + datetime.now().strftime(timef) + " Reporting delay: " + str(getDelay(lasttime)) + " seconds")
                else:
                    print("Quake mag " + mag + ". " + str(dist) + "km away, " + locname)
                saveLast(lasttime,lastid)

        else:
            print(Fore.RED + "Error Retreiving Quakes" + Style.RESET_ALL)
    time.sleep(5)