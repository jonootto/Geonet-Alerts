import requests
import json
from dateutil.parser import parse
from datetime import datetime, timezone
import time
from geopy import distance
from colorama import Fore, Style
import meshtastic
import meshtastic.tcp_interface
import time
import os
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO)
load_dotenv()

api = "https://api.geonet.org.nz/quake?MMI=3"
maxdist = 500 #km
minmag = 0
radioHostname = os.environ["RADIO_HOSTNAME"]
channel = int(os.environ.get("CHANNEL_INDEX",1))

timef = "%r %A %d %B %y"

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
        logging.error("Error:" + str(r.status_code))
    

def utc_to_local(utc_dt):
    #convert time into local time
    return utc_dt.replace(tzinfo=timezone.utc).astimezone(tz=None)

def readSaved():
    #load last saved event from disk
    f = open("last.txt", "r")
    return json.load(f)

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
    return



def sendMsg(msgtxt):
    #send message over spefified channel
    logging.info("Sending to mesh...")
    interface.sendText(msgtxt,channelIndex=channel)


lastQuakes = ""
savedEvent = readSaved()
savedTime = parse(savedEvent["timestamp"]).replace(tzinfo=None)
logging.warning("Starting up...")
logging.info("Last event "+ savedEvent["id"] +" at " + savedTime.strftime(timef))

try:
    logging.info("Connecting to radio...")
    interface = meshtastic.tcp_interface.TCPInterface(hostname=radioHostname)
    logging.info("Connected to radio: " + interface.getLongName())
except:
    logging.error("error connecting")
    quit()

while True:
    quakes = getQuakes()
    if quakes != lastQuakes:
        lastQuakes = quakes
        logging.info("New Data")
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
                    msg = str("Quake at " +lasttime.strftime(timef)+ "\nMag: " + mag + "\n" + str(dist) + "km from WLG\n" + locname)
                    logging.info(msg)
                    sendMsg(msg)
                    logging.info("Time now " + datetime.now().strftime(timef) + " Reporting delay: " + str(getDelay(lasttime)) + " seconds")
                else:
                    logging.info("Quake mag " + mag + ". " + str(dist) + "km away, " + locname)
                saveLast(lasttime,lastid)

        else:
            logging.error(Fore.RED + "Error Retreiving Quakes" + Style.RESET_ALL)

    time.sleep(5.0)