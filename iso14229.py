#! /usr/bin/python3
from controllerareanetwork import ControllerAreaNetwork
import itertools
import threading
import time

class AppLayer:
    def __init__(self, candevice, module):
        #module is the name of the module to communicate with (dict lookup)
        #candevice needs to be 'can0' or the like, needs set to correct
        #speed prior to calling function
        if isinstance(candevice,ControllerAreaNetwork):
            self.can = candevice
        elif candevice != "null":
            self.can = ControllerAreaNetwork(candevice)
        self.sendTP = 0
        self.TP_sema = threading.Semaphore() #used to keep tester present from
        #transmitting while other functions actively transmitting / listening
        self.tx_arb = module[0]
        self.rx_arb = module[1]
        self.description = module[2]
        self.ReadMemLenBytes = module[3][0]
        self.ReadMemAddrBytes = module[3][1]
        
    def TesterPresent(self):
        self.TP_sema.acquire()
        self.can.SendCAN(self.tx_arb, 8, [2, 0x3E, 0x00])
        [rxArb, rxDlc, rxData] = self.GetMultiFrame(self.tx_arb, self.rx_arb, .1)
        self.TP_sema.release()
        if len(rxData) < 1 or rxData[0] != 0x7E:
            return False
        else:
            return True 
 
    def TP_Thread(self):
        self.sendTP = 1
        while (self.sendTP==1):
            self.TesterPresent()
            time.sleep(1.0)
                    
    def DiagSession(self, level, seconds):
        if level > 0xFF:
            level = 0xFF
        elif level < 0:
            level = 0
        self.TP_sema.acquire()
        startTime = time.time()
        while time.time() - startTime < seconds:
            self.can.SendCAN(self.tx_arb, 8, [2, 0x10, 0x80 | level])
            time.sleep(.015)
        self.can.SendCAN(self.tx_arb, 8, [2, 0x10, level])
        [rxArbID, rxDlc, rxData] = self.can.RxCANByArbID(self.rx_arb, .5)
        self.TP_sema.release()
        if len(rxData) < 2 or rxData[1] != 0x50:
            return False
        else:
            if level > 0:
                threading.Thread(target=self.TP_Thread, daemon=True).start()
            else:
                self.sendTP = 0
            return True 

    def ReadMem(self, address, length):
        if self.ReadMemLenBytes == 0 or self.ReadMemAddrBytes == 0:
            print(self.description + ' does not have read format specified')
            return []
        Data = [0x23, ((self.ReadMemLenBytes<<4) & 0xF0) | (self.ReadMemAddrBytes & 0x0F)]
        Data.extend(self.ToArray(address, self.ReadMemAddrBytes))
        Data.extend(self.ToArray(length, self.ReadMemLenBytes))
        self.TP_sema.acquire()
        [rxArbID, rxDlc, rxData] = self.SendCAN_AppLayer(self.tx_arb, self.rx_arb, Data, 1)
        self.TP_sema.release()
        responseCode = 0
        memBytes = []
        if rxArbID != self.rx_arb or len(rxData) < 3:
            responseCode = -1
        elif rxData[0] == 0x7F and rxData[1] == 0x23:
            responseCode = rxData[2]
        elif len(rxData) >= length+1 and rxData[0] == 0x63:
            memBytes = rxData[1:1+length]
        else:
            responseCode = -1
        return [responseCode, memBytes]

    def GetSeed(self, level):
        self.TP_sema.acquire()
        [rxArbID, rxDlc, rxData] = self.SendCAN_AppLayer(self.tx_arb, self.rx_arb, [0x27, level], 1)
        if rxArbID != self.rx_arb or len(rxData) < 1 or rxData[0] == 0x7F:
            [rxArbID, rxDlc, rxData] = self.GetMultiFrame(self.tx_arb, self.rx_arb, 1)
        self.TP_sema.release()
        responseCode = 0
        seedBytes = []
        if rxArbID != self.rx_arb or len(rxData) < 2:
            responseCode = -1
        elif rxData[0] == 0x7F and rxData[1] == 0x27:
            if len(rxData) >= 3:
                responseCode = rxData[2]
            else:
                responseCode = -1
        elif rxData[0] == 0x67 and rxData[1] == level:
            seedBytes = rxData[2:]
        return [responseCode, seedBytes]

    def SendKey(self, level, keyBytes):
        Data = [0x27, level]
        Data.extend(keyBytes)
        self.TP_sema.acquire()
        [rxArbID, rxDlc, rxData] = self.SendCAN_AppLayer(self.tx_arb, self.rx_arb, Data, 1)
        self.TP_sema.release()
        responseCode = 0
        responseBytes = []
        if rxArbID != self.rx_arb or len(rxData) < 2:
            responseCode = -1
        elif rxData[0] == 0x7F and rxData[1] == 0x27:
            if len(rxData) >= 3:
                responseCode = rxData[2]
            else:
                responseCode = -1
        elif rxData[0] != 0x67 and rxData[1] != level:
            responseCode = -1
        return [responseCode, responseBytes]

    def ToArray(self, num, num_bytes):
        # Convert num to an array of bytes, of length num_bytes, padding with 0s in front
        byte_array = []
        if num_bytes < 1:
            return byte_array
        for i in range(num_bytes):
            byte_array.append((num >> (num_bytes-i-1)*8) & 0xFF)
        while len(byte_array) < num_bytes:
            byte_array.insert(0, 0x00)
        return byte_array

    def GetPID(self, pid):
        data = [0x22, (PID>> 8) & 0xFF, pid & 0xFF]
        resp = self.SendCAN_AppLayer(self.tx_arb, self.rx_arb, data)
        print(' '.join(map(str, [hex(k).lstrip("0x").zfill(2) for k in resp])).upper())
        return resp
    
    def GetVIN(self):
        resp = SendCAN_AppLayer(self.tx_arb, self.rx_arb, [0x09, 0x02])
        VINtxt = ''.join(map(chr,resp[1:]))
        print('VIN: ' + VINtxt)
        return VINtxt
        
    def SendCAN_AppLayer(self, arbTx, arbRx, Data, replyWaitSeconds):
        numBytes = len(Data)
        if numBytes < 8:
                self.can.SendCAN(arbTx, 8, [numBytes] + Data)
        else:
            MsgNeeded = 1
            bytesLeft = numBytes - 6
            while bytesLeft > 0:
                MsgNeeded = MsgNeeded + 1
                bytesLeft = bytesLeft - 7
            MsgHeader = [((numBytes>>8) & 0x0F ) | 0x10, numBytes & 0xFF]
            self.can.SendCAN(arbTx, 8, MsgHeader + Data[0:6])

            # This next section will keep trying to receive the 0x30 message for 1 sec, in case other messages are received also
            startTime = time.time()
            rxFrame = self.can.RxCANByArbID(arbRx, 1)
            if rxFrame[0] != arbRx:
                return [-1, 0, []]
            while len(rxFrame[2]) < 1 or rxFrame[2][0] != 0x30:
                elapsedTime = time.time() - startTime
                if elapsedTime > 1:
                    return [-1, 0, []]
                rxFrame = self.can.RxCANByArbID(arbRx, 1-elapsedTime)
                if rxFrame[0] != arbRx:
                    return [-1, 0, []]

            MsgNum = 0x21
            startInd = 6
            
            for index in range(MsgNeeded-1):
                BytesToRead = 7
                if(startInd+BytesToRead) > numBytes:
                    BytesToRead = numBytes - startInd
                time.sleep(0.01)
                self.can.SendCAN(arbTx,8,[MsgNum] + Data[startInd:(startInd+BytesToRead)])
                MsgNum = MsgNum + 1
                startInd = startInd + BytesToRead
                if MsgNum > 0x2F:
                    MsgNum = 0x20

        [rxArbID, rxDlc, rxData] = [-1, 0, []]
        if replyWaitSeconds > 0:
            [rxArbID, rxDlc, rxData] = self.GetMultiFrame(arbTx, arbRx, replyWaitSeconds) # get multi frame removes the data size element. 
        return [rxArbID, rxDlc, rxData]

    def GetMultiFrame(self, talkArb, listenArb, timeOut):
        [rxArbID, rxDlc, rxData] = self.can.RxCANByArbID(listenArb, timeOut)
        if rxArbID != listenArb or rxDlc != 8 or len(rxData) < 1 or rxData[0] >> 4 != 1:
            if len(rxData) > 1:
                rxData = rxData[1:1+rxData[0]]
            return [rxArbID, rxDlc, rxData]
        bytesLeft = (((rxData[0] & 0x0F) << 8) | (rxData[1])) - 6
        data = rxData[2:]
        MsgNum = 0x21
        self.can.SendCAN(talkArb, 8, [0x30, 0x00, 0x00])
        while bytesLeft > 0:
            [rxArbID, rxDlc, rxData] = self.can.RxCANByArbID(listenArb, timeOut)
            if rxArbID != listenArb:
                return [rxArbID, rxDlc, rxData]
            if rxDlc != 8 or rxData[0] != MsgNum:
                continue
            if bytesLeft < 7:
                data.extend(rxData[1:bytesLeft+1])
                bytesLeft = 0
            else:
                data.extend(rxData[1:])
                bytesLeft = bytesLeft - 7
            MsgNum = MsgNum + 1
            if MsgNum == 0x30:
                MsgNum = 0x20
        return [listenArb, 0x10, data]

    def RxData(self, arbID, data, timeOut):
        #Wait for message from arbID that starts with 'data' (skipping length byte)
        elapsedTime = 0
        start_time = time.time()
        while elapsedTime < timeOut:
            [rxArbID, rxDlc, rxData] = self.can.RxCANByArbID(arbID, timeOut-elapsedTime)
            if rxArbID == arbID and len(rxData) >= len(data) and rxData[1:1+len(data)] == data:
                return [rxArbID, rxDlc, rxData[1:]]
            elapsedTime = time.time() - start_time
        return [-1, 0, []]
