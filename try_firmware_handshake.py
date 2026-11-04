import socket
import time
import sys
import struct

IP = "192.168.1.199"
PORT = 5003

# Message 1 from firmware
# F0 00 01 73 7D 00 0E 00 00 00 00 00 00 00 00 00 00 00 00 08 7F 7F 20 57 30 12 04 60 4F F7
MSG1 = bytes.fromhex("F00001737D000E0000000000000000000000000000087F7F2057301204604FF7")

# Message 1 with 00 00 instead of 00 0E
MSG1_MOD = bytes.fromhex("F00001737D00000000000000000000000000000000087F7F2057301204604FF7")

# Get Preset Name Command (Reconstructed)
# F0 00 01 73 7D + 19x00 + 0C + 03 03 02 05 04 01 09 01 04 01 01 02 + Cksum + F7
# Body for checksum: 19x00 + 0C + Data
# Wait, checksum calculation in script was: 128 - (sum(body) % 128)
# Body includes the 19 zeros?
# In script: body = foo + txn + clen + cmd_data
# foo=12x00. devid=7x00. Total 19x00.
# txn=2 bytes. clen=1 byte?
# Let's look at script again.
# sysex_preset_name: body = foo + txn_bytes + clen + cmd_data
# foo=12 bytes.
# devid is part of header in script: F0 + mfid + msgcls + devid + body...
# devid=7 bytes.
# So body starts after devid.
# Body = 12x00 + txn(2) + clen(1) + cmd(12).
# Total body len = 12 + 2 + 1 + 12 = 27 bytes.
# Checksum is calculated on these 27 bytes.

def calculate_checksum(data):
    return (128 - (sum(data) % 128)) & 0x7F

def build_get_preset_sysex(preset_idx):
    header = bytes.fromhex("F0 00 01 73 7D 00 00 00 00 00 00 00") # F0 + Mfr + 7D + 7x00 (DevID)
    # Wait, devid is 7 bytes. 00 01 73 7D is 4 bytes.
    # F0 00 01 73 7D 00 00 00 00 00 00 00 (12 bytes total?)
    # F0 (1) + 00 01 73 (3) + 7D (1) + 00*7 (7) = 12 bytes. Correct.
    
    # Body
    # foo (12 bytes 00)
    # txn (2 bytes) -> Let's use 00 01
    # clen (1 byte) -> 0C (12 bytes of cmd)
    # cmd (12 bytes) -> 03 03 02 05 04 01 09 01 04 01 01 02 (Preset 1)
    
    body = bytes([0]*12) + bytes([0, 1]) + bytes([0x0C]) + bytes([0x03, 0x03, 0x02, 0x05, 0x04, 0x01, 0x09, preset_idx, 0x04, 0x01, 0x01, 0x02])
    
    cksum = calculate_checksum(body)
    
    return header + body + bytes([cksum]) + b"\xF7"

GET_PRESET_CMD = build_get_preset_sysex(1)

def send_udp(sock, ip, port, data, desc):
    print(f"Sending {desc} to {ip}:{port} ({len(data)} bytes)")
    sock.sendto(data, (ip, port))

def invite(sock, ip, port, name="Unlocker"):
    token_val = 0x12345678
    ssrc = 0x11223344
    sig=b"\xff\xff"; cmd=b"IN"; ver=struct.pack("!I",2); token=struct.pack("!I",token_val); ssrc_bytes=struct.pack("!I",ssrc)
    pkt=sig+cmd+ver+token+ssrc_bytes+name.encode()+b"\x00"
    send_udp(sock, ip, port, pkt, "AppleMIDI Invitation")

def listen(sock, duration=2):
    end = time.time() + duration
    while time.time() < end:
        try:
            data, addr = sock.recvfrom(1024)
            print(f"Received from {addr}: {data.hex()}")
            if data[0:2] == b"\xff\xff":
                print(f"  AppleMIDI: {data[2:4]}")
        except socket.timeout:
            pass

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', 0))
    sock.settimeout(0.5)
    
    print(f"Local port: {sock.getsockname()[1]}")
    
    # 1. Send Raw Firmware Message 1
    send_udp(sock, IP, PORT, MSG1, "Firmware Msg 1 (Raw)")
    listen(sock, 1)
    
    # 2. Send Modified Firmware Message 1
    send_udp(sock, IP, PORT, MSG1_MOD, "Modified Msg 1 (Raw)")
    listen(sock, 1)
    
    # 2b. Send Get Preset Name Command (Raw)
    send_udp(sock, IP, PORT, GET_PRESET_CMD, "Get Preset Name (Raw)")
    listen(sock, 1)

    # 2c. Send Firmware Msg 1 to Port 5006 (Raw)
    send_udp(sock, IP, 5006, MSG1, "Firmware Msg 1 to Port 5006 (Raw)")
    listen(sock, 1)

    # 2d. Send Firmware Msg 1 to Broadcast (Port 5003)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    send_udp(sock, "255.255.255.255", PORT, MSG1, "Firmware Msg 1 to Broadcast:5003")
    listen(sock, 1)
    
    # 3. Try Invite
    invite(sock, IP, PORT)
    listen(sock, 2)
    
    # 4. Try sending Msg 1 encapsulated in RTP-MIDI (blindly)
    # RTP Header: 80 61 Seq TS SSRC
    rtp_hdr = struct.pack("!BBHII", 0x80, 0x61, 1, 0, 0x11223344)
    payload = b"\x00" + MSG1 # 00 is MIDI command section flags?
    packet = rtp_hdr + payload
    send_udp(sock, IP, PORT, packet, "RTP-MIDI Encapsulated Msg 1")
    listen(sock, 1)

    sock.close()

if __name__ == "__main__":
    main()
