#! /usr/bin/python3
#Author: @carfucar
import socket
import struct
import math
import time

class ControllerAreaNetwork:
    def __init__(self, module):
        #needs to call command line functions to setup the module
        #module needs to be 'can0' or the like
        self.CanSock = socket.socket(socket.AF_CAN, socket.SOCK_RAW, socket.CAN_RAW)
        #self.CanSock.setsockopt(socket.SOL_CAN_RAW, socket.CAN_RAW_FILTER, 
        #         struct.pack("II", 0x7E8, 0x7F0)) 
                 #this filter is set for diagnostics on 0x700 level
        self.CanSock.bind((module,))
        self.can_frame_fmt = "=IB3x8s"
    description = "Functions for CAN bus operation"
    author = "DAT 2013 08 21"
        
    def SendCAN(self, Arb, DLC, Data):
        #canMsgStr = str(bytearray(Data))
        canMsgStr = bytearray(Data)
        canMsgStr = canMsgStr.ljust(8, b'\x00')
        pkdMsg = struct.pack(self.can_frame_fmt, Arb, DLC, canMsgStr)
        self.CanSock.send(pkdMsg)
    
    def printFrame(self, arb, dlc, data):
        frameString = "%03x" % arb
        frameString = frameString + "   " + "[" + "%01x" % dlc + "] "
        for element in data:
            frameString = frameString + " %02x" % element
        print(frameString)

    def RxCAN(self, timeOut):
        self.CanSock.settimeout(timeOut) # timeOut in seconds as a timeout for rx
        try:
            cf, addr = self.CanSock.recvfrom(16)
        except socket.timeout:
            return[-1,0,[]]
        can_id, can_dlc, data = struct.unpack(self.can_frame_fmt, cf)
        data = data[:can_dlc]
        data = list(data)
        #switches data from a byte array to a list
        #to print result in hex: [hex(k) for k in data]
        return [can_id, can_dlc, data]

    def RxCANByArbID(self, Arb, timeOut):
        #Wait for the next message with ArbID==Arb
        elapsedTime = 0
        start_time = time.time()
        while elapsedTime < timeOut:
            resp = self.RxCAN(timeOut - elapsedTime)
            if resp[0] == Arb:
                return resp
            elapsedTime = time.time() - start_time
        return [-1,0,[]]
