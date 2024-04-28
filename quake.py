import requests
import json
from dateutil.parser import parse
from datetime import datetime, timezone
import time
from geopy import distance
from colorama import Fore, Back, Style


api = "https://api.geonet.org.nz/quake?MMI=-1"
maxdist = 300

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

def saveLast(timestamp,id):
    data = {
        "timestamp" : str(timestamp),
        "id" : str(id)
    }
    with open('last.txt', 'w') as f:
        json.dump(data, f, ensure_ascii=False)
    return


lastQuakes = ""
savedEvent = readSaved()
savedTime = parse(savedEvent["timestamp"]).replace(tzinfo=None)
print("Last event "+ savedEvent["id"] +" at " + savedTime.strftime("%r %A %d %B %y"))

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
                    print("New Quake: " + lastid + " magnitude: " + mag + " at " + lasttime.strftime("%r %A %d %B %y") + " " + str(dist) + "km from Wellington, " + locname )
                    timenow = datetime.now().replace(tzinfo=None)
                    timediff = (timenow - savedTime).total_seconds()
                    delay = round(timediff)
                    print("Time now " + datetime.now().strftime("%r %A %d %B %y") + " Reporting delay: " + str(delay) + " seconds")
                else:
                    print("Quake " + str(dist) + "km away, " + locname)
                saveLast(lasttime,lastid)

        else:
            print(Fore.RED + "Error Retreiving Quakes" + Style.RESET_ALL)
    time.sleep(5)