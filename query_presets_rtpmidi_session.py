#!/usr/bin/env python3
"""
Improved RTP-MIDI preset query keeping single AppleMIDI session open.
Attempts multiple SysEx queries over same session with incrementing RTP sequence numbers.
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
    # Captured from Auracle X:
    # F0 00 01 73 7D 00..00 (13 bytes) SeqHi SeqLo Len Cmd1..Cmd6 Cmd7 Preset Cmd8..Cmd11 Cksum F7
    # Cmd1..6 = 03 03 02 05 04 01
    # Cmd7 = 09 (or 01?)
    # Preset = 01..20
    # Cmd8..11 = 04 01 01 02
    
    mfid = b"\x00\x01\x73"; msgcls = b"\x7d"; devid = b"\x00"*7; foo = b"\x00"*12
    
    # Construct the command body
    # Based on Packet 14: 03 03 02 05 04 01 01 00 04 01 01 02
    # Wait, Packet 14 had: 03 03 02 05 04 01 01 00 04 01 01 02
    # Packet 18 had:       03 03 02 05 04 01 09 01 04 01 01 02
    # Packet 20 had:       03 03 02 05 04 01 09 02 04 01 01 02
    
    # It seems the byte before the preset index is 09 (except for the first one?)
    # Let's try using 09.
    
    cmd_prefix = bytes([0x03, 0x03, 0x02, 0x05, 0x04, 0x01])
    cmd_mid = bytes([0x09]) # This seems to be the "Get" command variant?
    preset_byte = bytes([preset])
    cmd_suffix = bytes([0x04, 0x01, 0x01, 0x02])
    
    cmd_data = cmd_prefix + cmd_mid + preset_byte + cmd_suffix
    
    # Length of cmd_data is 12 bytes (0x0C)
    clen = bytes([len(cmd_data)]) # 1 byte length?
    
    # Transaction ID (2 bytes)
    txn_bytes = encode7(txn, 2)
    
    body = foo + txn_bytes + clen + cmd_data
    
    syx = b"\xF0" + mfid + msgcls + devid + body + bytes([chksum(body)]) + b"\xF7"
    return syx

# Firmware Handshake Message (Msg 1)
# F0 00 01 73 7D 00 0E 00 00 00 00 00 00 00 00 00 00 00 00 08 7F 7F 20 57 30 12 04 60 4F F7
FIRMWARE_HANDSHAKE = bytes.fromhex("F00001737D000E0000000000000000000000000000087F7F2057301204604FF7")

class AppleMIDISession:
    def __init__(self, ip, port):
        self.ip=ip; self.port=port
        self.sock=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.hijacking = False
        try:
            # self.sock.bind(('', 15005)) # Bind to local port 15005 (match capture)
            # print("Bound to local port 15005 - Attempting Hijack")
            # self.hijacking = True
            # Force random port to start fresh
            self.sock.bind(('', 0))
            print(f"Bound to random port {self.sock.getsockname()[1]} - Attempting Fresh Invitation")
            self.hijacking = False
        except Exception as e:
            print(f"Could not bind to local port 15005: {e}")
            # Try random
            self.sock.bind(('', 0))
            print(f"Bound to random port {self.sock.getsockname()[1]} - Attempting Invitation")
            self.hijacking = False
        
        self.sock.settimeout(3)
        self.sequence=0 # Start with lower sequence
        self.ssrc = 0x0000000B # Mimic Auracle X SSRC

    def invite(self,name="PresetQuerySess"):
        # Standard AppleMIDI Invitation
        # Try a new random token to start fresh
        import random
        token_val = random.randint(0, 0xFFFFFFFF)
        # Use a random SSRC too?
        self.ssrc = random.randint(0, 0xFFFFFFFF)
        
        sig=b"\xff\xff"; cmd=b"IN"; ver=struct.pack("!I",2); token=struct.pack("!I",token_val); ssrc=struct.pack("!I",self.ssrc)
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
        # RTP header: V=2,P=0,X=0,CC=0 -> 0x80; PT=97 -> 0x61
        self.sequence=(self.sequence+1)&0xFFFF
        timestamp=int(time.time()*1000)&0xFFFFFFFF
        rtp=struct.pack("!BBHII",0x80,0x61,self.sequence,timestamp,self.ssrc)
        midi_flags=0x00
        payload=bytes([midi_flags])+syx
        packet=rtp+payload
        self.sock.sendto(packet,(self.ip,self.port))
        print(f"Sent SysEx: {len(packet)} bytes")

    def recv_packets(self, duration=5.0):
        end=time.time()+duration
        packets=[]
        while time.time()<end:
            try:
                data,_=self.sock.recvfrom(2048)
                packets.append(data)
                # Print raw packet for debugging
                # print(f"RX: {data.hex()}")
            except socket.timeout:
                pass
        return packets
    def send_sync(self):
        # AppleMIDI CK (Clock Sync)
        # FFFF 434B (CK) ...
        # Just send a dummy sync packet similar to capture
        # ffff434b 0000000b 00000000 00000000 000767f0 00000000 00000000 00000000 00000000
        pkt = bytes.fromhex("ffff434b0000000b0000000000000000000767f000000000000000000000000000000000")
        self.sock.sendto(pkt, (self.ip, self.port))
        print("Sent Sync Packet")
        
        # Also send RS (Receiver Feedback) just in case
        # ffff 5253 (RS) ...
        pkt_rs = bytes.fromhex("ffff52530000000b00000000")
        self.sock.sendto(pkt_rs, (self.ip, self.port))
        print("Sent RS Packet")

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
# Try to invite if not hijacking
if not sess.hijacking:
    # Loop until accepted
    print("Attempting to invite (looping)...")
    connected = False
    for i in range(10):
        if sess.invite(name="Auracle"):
            connected = True
            break
        time.sleep(1)
    
    if not connected:
        print("Cannot open session after 10 attempts; aborting.")
        sys.exit(1)
else:
    # Even if hijacking, maybe send an invite just in case the session timed out?
    # But use the same SSRC and Token as capture?
    # Let's try sending an invite with the captured SSRC
    print("Sending Re-Invite with captured SSRC...")
    sess.invite()

sess.send_sync()
time.sleep(0.1)

# Try sending Firmware Handshake (Msg 1)
print("Sending Firmware Handshake (Msg 1)...")
sess.send_sysex(FIRMWARE_HANDSHAKE)
time.sleep(0.5)

results={}

# 1. Number of presets
print("Query: Number of presets")
num_sysex=sysex_num_presets(1)
sess.send_sysex(num_sysex)
resp_packets=sess.recv_packets()
print(f"Received {len(resp_packets)} packets for num_presets")
for p in resp_packets:
    if len(p)>20 and p[12]==0x00 and p[13]==0xF0: # crude locate sysex start maybe offset
        ascii_parts=extract_ascii(p)
        if ascii_parts:
            print("ASCII parts:",ascii_parts)

# 2. Current preset
print("Query: Current preset")
cur_sysex=sysex_current_preset(2)
sess.send_sysex(cur_sysex)
resp_packets=sess.recv_packets()
print(f"Received {len(resp_packets)} packets for current preset")

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
            # Filter out generic strings
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
    print("No preset names extracted; likely network config requires different encapsulation or a different command class.")
