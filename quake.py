import requests
import json
from dateutil.parser import parse
from datetime import datetime, timezone
import time
from geopy import distance

api = "https://api.geonet.org.nz/quake?MMI=-1"

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

def readLast():
    f = open("last.txt", "r")
    return f.read()

def writeLast(timestamp):
    f = open("last.txt", "w")
    f.write(timestamp)
    f.close()
    return

print("Last event at " + parse(readLast()).strftime("%r %A %d %B %y"))

while True:
    quakes = getQuakes()
    if quakes:
        lastevent = quakes['features'][0]
        lasttime = utc_to_local(parse(lastevent['properties']['time']))


        if str(lasttime) != readLast():
            print("New Data")
            print("New Event at " + lasttime.strftime("%r %A %d %B %y"))
            lastpos = getPos(lastevent['geometry']['coordinates'])
            print(str(dstWlg(lastpos)) + "km from Wellington")
            print("Time now " + datetime.now().strftime("%r %A %d %B %y"))
            writeLast(str(lasttime))
    else:
        print("Error")
    time.sleep(5)