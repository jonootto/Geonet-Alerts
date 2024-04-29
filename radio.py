import meshtastic
import meshtastic.tcp_interface
from pubsub import pub
import time

#def onReceive(packet, interface): # called when a packet arrives
#    print(f"Received: {packet}")

def onConnection(interface, topic=pub.AUTO_TOPIC):
    print("Connected")
    interface.sendText("test",channelIndex=1)

#pub.subscribe(onReceive, "meshtastic.receive")
pub.subscribe(onConnection, "meshtastic.connection.established")
interface = meshtastic.tcp_interface.TCPInterface(hostname='192.168.1.94')


while True:
    time.sleep(1000)
interface.close()
