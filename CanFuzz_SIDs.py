#! /usr/bin/python3
# Author: carfucar
from controllerareanetwork import ControllerAreaNetwork
import socket
import struct
import sys
import time

def UpdateProgress(start, end, value):
    percentage = int((value/(end - start))*100)
    sys.stdout.write("\r%d%%" %percentage)
    sys.stdout.flush()

if len(sys.argv) < 3:
    print("Usage: CanFuzz_SIDs.py <device name> <arbID>")
    print("Ex: ./CanFuzz_SIDs.py can0 7DF")
    print("(Note - CAN device needs to be set up first)")
    sys.exit()

can = ControllerAreaNetwork(sys.argv[1])
print("Fuzzing...")
arbid = int(sys.argv[2], 16);
sid = 0;
for sid in range(0, 0x100):
    can.SendCAN(arbid, 8, [0x2, sid, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
    start_time = time.time()
    UpdateProgress(0, 0x100, sid)
    while time.time() - start_time < .1:  # Wait for response for .1 second
        time.time()
UpdateProgress(0,0x100,0x100)
