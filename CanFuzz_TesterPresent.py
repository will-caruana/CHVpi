#! /usr/bin/python3
from controllerareanetwork import ControllerAreaNetwork
import socket
import struct
import sys
import time

def UpdateProgress(start, end, value):
    percentage = int((value/(end - start))*100)
    sys.stdout.write("\r%d%%" %percentage)
    sys.stdout.flush()

if len(sys.argv) < 2:
    print("Usage: CanFuzz_TesterPresent.py <device name>")
    print("Ex: ./CanFuzz_TesterPresent.py can0")
    print("(Note - CAN device needs to be set up first)")
    sys.exit()

can = ControllerAreaNetwork(sys.argv[1])
print("Fuzzing tester present...")
arbid = 0;
responsePairs = []
for arbid in range(0, 0x800):
    can.SendCAN(arbid, 8, [0x2, 0x3E, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
    start_time = time.time()
    UpdateProgress(0, 0x800, arbid)
    while time.time() - start_time < .1:  # Wait for response for .1 second
        [rxArbID, rxDlc, rxData] = can.RxCAN(.1)
        if rxArbID < 0 or rxDlc <= 0:
            continue
        if rxDlc >= 2 and len(rxData) >=2 and rxData[1] == 0x7E:
            responsePairs.append([arbid, rxArbID])
        elif rxDlc >= 3 and len(rxData) >= 3 and rxData[1] == 0x7F and rxData[2] == 0x3E:
            responsePairs.append([arbid, rxArbID])
UpdateProgress(0,0x800,0x800)
if len(responsePairs) == 0:
    print ("\nNo responses received")
else:
    print("\nTx ArbID | Rx ArbID")
    for i in range(0, len(responsePairs)):
        print(format(responsePairs[i][0],'03x') + "        " + format(responsePairs[i][1], '03x')) 
