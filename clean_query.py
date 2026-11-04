#!/usr/bin/env python3
"""
Clean RTP-MIDI preset query.
Binds to a random port and establishes a standard AppleMIDI session.
Use this when Auracle is NOT using the Ethernet port (e.g. USB connected).
"""
import socket, struct, sys, time

IP = sys.argv[1] if len(sys.argv) > 1 else "192.168.1.199"
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 5003 # Default to 5003 (Control Port)

# Simple 7-bit length encoder
def encode7(val, size=2):
    bd = bytearray()
    while val > 0:
        bd.insert(0, val & 0x7f)
        val >>= 7
    while len(bd) < size:
        bd.insert(0, 0x00)
    return bd

def chksum(data):
    cs = 128 - (sum(data) % 128)
    return 0 if cs == 128 else cs

def makearg(data):
    arg = bytearray(data)
    arg.insert(0, len(arg) + 1)
    return arg

# Build SysEx for different queries using mioctl patterns
def sysex_num_presets(txn=1):
    mfid = b"\x00\x01\x73"; msgcls = b"\x7d"; devid = b"\x00"*7; foo = b"\x00"*12
    flags = 0x03; cmd = 0x02; nargs = 0x01; arg1 = makearg([0x01,0x01,0x14])
    cmd_data = bytes([flags,cmd,nargs]) + arg1
    clen = encode7(len(cmd_data),2)
    body = foo + encode7(txn,2) + clen + cmd_data
    syx = b"\xF0" + mfid + msgcls + devid + body + bytes([chksum(body)]) + b"\xF7"
    return syx

def sysex_current_preset(txn=2):
    mfid = b"\x00\x01\x73"; msgcls = b"\x7d"; devid = b"\x00"*7; foo = b"\x00"*12
    flags=0x03; cmd=0x03; nargs=0x01; arg1 = makearg([0x01,0x01,0x01])
    cmd_data = bytes([flags,cmd,nargs]) + arg1
    clen = encode7(len(cmd_data),2)
    body = foo + encode7(txn,2) + clen + cmd_data
    syx = b"\xF0" + mfid + msgcls + devid + body + bytes([chksum(body)]) + b"\xF7"
    return syx

def sysex_preset_name(preset, txn):
    mfid = b"\x00\x01\x73"; msgcls = b"\x7d"; devid = b"\x00"*7; foo = b"\x00"*12
    cmd_prefix = bytes([0x03, 0x03, 0x02, 0x05, 0x04, 0x01])
    cmd_mid = bytes([0x09]) 
    preset_byte = bytes([preset])
    cmd_suffix = bytes([0x04, 0x01, 0x01, 0x02])
    cmd_data = cmd_prefix + cmd_mid + preset_byte + cmd_suffix
    clen = bytes([len(cmd_data)])
    txn_bytes = encode7(txn, 2)
    body = foo + txn_bytes + clen + cmd_data
    syx = b"\xF0" + mfid + msgcls + devid + body + bytes([chksum(body)]) + b"\xF7"
    return syx

class AppleMIDISession:
    def __init__(self, ip, port):
        self.ip=ip; self.port=port
        self.sock=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Always bind random for clean session
        self.sock.bind(('', 0))
        print(f"Bound to random port {self.sock.getsockname()[1]}")
        
        self.sock.settimeout(3)
        self.sequence=0 
        self.ssrc = 0x12345678 # Use our own SSRC

    def invite(self,name="CleanQuerySess"):
        # Standard AppleMIDI Invitation
        sig=b"\xff\xff"; cmd=b"IN"; ver=struct.pack("!I",2); token=struct.pack("!I",0x11223344); ssrc=struct.pack("!I",self.ssrc)
        pkt=sig+cmd+ver+token+ssrc+name.encode()+b"\x00"
        self.sock.sendto(pkt,(self.ip,self.port))
        try:
            data,_=self.sock.recvfrom(256)
            if data[0:2]==b"\xff\xff" and data[2:4]==b"OK":
                print(f"Session accepted: name={data[16:].decode(errors='ignore').strip(chr(0))}")
                self.sock.settimeout(0.5)
                return True
            print(f"Invitation rejected. Response: {data.hex()}")
            if len(data) > 4:
                 print(f"Type: {data[2:4]}")
        except socket.timeout:
            print("Invitation timeout")
        return False

    def send_sysex(self, syx:bytes):
        self.sequence=(self.sequence+1)&0xFFFF
        timestamp=int(time.time()*1000)&0xFFFFFFFF
        rtp=struct.pack("!BBHII",0x80,0x61,self.sequence,timestamp,self.ssrc)
        midi_flags=0x00
        payload=bytes([midi_flags])+syx
        packet=rtp+payload
        self.sock.sendto(packet,(self.ip,self.port))

    def recv_packets(self, duration=1.5):
        end=time.time()+duration
        packets=[]
        while time.time()<end:
            try:
                data,_=self.sock.recvfrom(2048)
                packets.append(data)
            except socket.timeout:
                pass
        return packets
    
    def send_sync(self):
        # AppleMIDI CK (Clock Sync)
        pkt = bytes.fromhex("ffff434b") + struct.pack("!I", self.ssrc) + bytes(24) # Padding
        self.sock.sendto(pkt, (self.ip, self.port))

    def close(self):
        self.sock.close()

# Parse responses for ASCII segments
def extract_ascii(data:bytes):
    ascii_chunks=[]
    cur=b""
    for b in data:
        if 32<=b<127:
            cur+=bytes([b])
        else:
            if len(cur)>=3:
                ascii_chunks.append(cur.decode())
            cur=b""
    if len(cur)>=3:
        ascii_chunks.append(cur.decode())
    return ascii_chunks

print(f"Connecting to RTP-MIDI session {IP}:{PORT}\n")

sess=AppleMIDISession(IP,PORT)
if not sess.invite():
    print("Cannot open session; aborting.")
    sys.exit(1)

sess.send_sync()
time.sleep(0.1)

results={}

# 3. Preset names 1..10
for preset in range(1,11):
    print(f"Query: Preset {preset} name")
    pn_sysex=sysex_preset_name(preset,10+preset)
    sess.send_sysex(pn_sysex)
    resp_packets=sess.recv_packets()
    if not resp_packets:
        print("  (no packets)")
        continue
    extracted=[]
    for pkt in resp_packets:
        ascii_parts=extract_ascii(pkt)
        for part in ascii_parts:
            if "mioXL" in part or "C1F" in part:
                continue
            extracted.append(part)
    if extracted:
        results[preset]=extracted[-1]
        print(f"  Name guess: {results[preset]}")
    else:
        print("  (no ascii name)")

sess.close()

print("\n==== PRESET SUMMARY (heuristic) ====\n")
if results:
    for k in sorted(results):
        print(f"Preset {k}: {results[k]}")
else:
    print("No preset names extracted.")
