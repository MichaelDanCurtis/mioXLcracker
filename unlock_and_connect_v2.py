import socket
import time
import sys
import struct
import threading

IP = "192.168.1.199"

# Firmware Handshake (Msg 1)
FIRMWARE_HANDSHAKE = bytes.fromhex("F00001737D000E0000000000000000000000000000087F7F2057301204604FF7")

class AppleMIDISession:
    def __init__(self, ip, port):
        self.ip=ip; self.port=port
        self.sock=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('', 0))
        self.sock.settimeout(1)
        self.sequence=0
        self.ssrc = 0x11223344

    def invite(self, name="Auracle"):
        token_val = 0x12345678
        sig=b"\xff\xff"; cmd=b"IN"; ver=struct.pack("!I",2); token=struct.pack("!I",token_val); ssrc=struct.pack("!I",self.ssrc)
        pkt=sig+cmd+ver+token+ssrc+name.encode()+b"\x00"
        self.sock.sendto(pkt,(self.ip,self.port))
        try:
            data,_=self.sock.recvfrom(256)
            if data[0:2]==b"\xff\xff" and data[2:4]==b"OK":
                return True
        except socket.timeout:
            pass
        return False

    def send_sysex(self, syx):
        self.sequence=(self.sequence+1)&0xFFFF
        timestamp=int(time.time()*1000)&0xFFFFFFFF
        rtp=struct.pack("!BBHII",0x80,0x61,self.sequence,timestamp,self.ssrc)
        payload=b"\x00"+syx
        packet=rtp+payload
        self.sock.sendto(packet,(self.ip,self.port))

    def keep_alive(self):
        while True:
            pkt = bytes.fromhex("ffff434b0000000b0000000000000000000767f000000000000000000000000000000000")
            self.sock.sendto(pkt, (self.ip, self.port))
            time.sleep(5)

def main():
    print("Step 1: Connect to 5006...")
    sess6 = AppleMIDISession(IP, 5006)
    if sess6.invite():
        print("Connected to 5006.")
        t = threading.Thread(target=sess6.keep_alive, daemon=True)
        t.start()
        
        print("Step 2: Send Handshake on 5006...")
        sess6.send_sysex(FIRMWARE_HANDSHAKE)
        time.sleep(1)
        
        print("Step 3: Try to Connect to 5003...")
        sess3 = AppleMIDISession(IP, 5003)
        if sess3.invite():
            print("SUCCESS! Connected to 5003!")
        else:
            print("Failed to connect to 5003.")
    else:
        print("Failed to connect to 5006.")

if __name__ == "__main__":
    main()
