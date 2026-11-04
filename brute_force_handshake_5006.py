import socket
import time
import sys
import struct

IP = "192.168.1.199"
PORT = 5006

def parse_hex_string(hex_str):
    return bytes.fromhex(hex_str)

def load_messages(filename):
    with open(filename, 'r') as f:
        lines = f.readlines()
    messages = []
    for line in lines:
        if "Raw:" in line:
            raw = line.split("Raw:")[1].strip()
            messages.append(parse_hex_string(raw))
    return messages

# Get Preset Name Command (from query_presets_rtpmidi_session.py)
# F0 00 01 73 7D + 19x00 + 0C + 03 03 02 05 04 01 09 01 04 01 01 02 + Cksum + F7
def build_get_preset_sysex(preset_idx):
    header = bytes.fromhex("F0 00 01 73 7D 00 00 00 00 00 00 00") 
    body = bytes([0]*12) + bytes([0, 1]) + bytes([0x0C]) + bytes([0x03, 0x03, 0x02, 0x05, 0x04, 0x01, 0x09, preset_idx, 0x04, 0x01, 0x01, 0x02])
    cksum = (128 - (sum(body) % 128)) & 0x7F
    return header + body + bytes([cksum]) + b"\xF7"

GET_PRESET_CMD = build_get_preset_sysex(1)

class AppleMIDISession:
    def __init__(self, ip, port):
        self.ip=ip; self.port=port
        self.sock=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('', 0))
        self.sock.settimeout(0.2) # Fast timeout
        self.sequence=0
        self.ssrc = 0x11223344

    def invite(self, name="Auracle"):
        token_val = 0x12345678
        sig=b"\xff\xff"; cmd=b"IN"; ver=struct.pack("!I",2); token=struct.pack("!I",token_val); ssrc=struct.pack("!I",self.ssrc)
        pkt=sig+cmd+ver+token+ssrc+name.encode()+b"\x00"
        self.sock.sendto(pkt,(self.ip,self.port))
        try:
            self.sock.settimeout(2)
            data,_=self.sock.recvfrom(256)
            self.sock.settimeout(0.2)
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

    def recv_packets(self):
        packets=[]
        try:
            while True:
                data,_=self.sock.recvfrom(2048)
                packets.append(data)
        except socket.timeout:
            pass
        return packets

def main():
    print("Loading messages...")
    msgs = load_messages("firmware_sysex.txt")
    short_msgs = [m for m in msgs if len(m) < 50]
    print(f"Loaded {len(short_msgs)} short messages.")
    
    sess = AppleMIDISession(IP, PORT)
    print(f"Connecting to {IP}:{PORT}...")
    if not sess.invite():
        print("Failed to connect.")
        return

    print("Connected. Brute forcing handshake...")
    
    for i, msg in enumerate(short_msgs):
        # Send Candidate Handshake
        sess.send_sysex(msg)
        
        # Send Query
        sess.send_sysex(GET_PRESET_CMD)
        
        # Listen
        pkts = sess.recv_packets()
        if len(pkts) > 0:
            print(f"SUCCESS! Received {len(pkts)} packets after Message {i} (Len {len(msg)})")
            print(f"Handshake Candidate: {msg.hex()}")
            # Print response
            for p in pkts:
                print(f"Response: {p.hex()}")
            break
            
        if i % 10 == 0:
            print(f"Tried {i} messages...")
            
    print("Done.")

if __name__ == "__main__":
    main()
