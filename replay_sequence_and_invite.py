#!/usr/bin/env python3
"""
Replay a sequence of SysEx messages (selected from firmware output) via RTP (port 5006)
and then attempt to invite port 5003 using the same source socket to test whether a sequence unlocks port 5003.
"""
import socket
import struct
import time
from pathlib import Path
import re

IP = '192.168.1.199'
PORT_SEND = 5006
PORT_CHECK = 5003

# read firmware messages and pick those containing the '08 7F 7F' pattern (short messages found earlier)

def parse_msgs(file):
    msgs = []
    with open(file, 'r') as f:
        for line in f:
            if 'Raw:' in line:
                raw = line.split('Raw:')[-1].strip()
                raw_clean = re.sub('[^0-9a-fA-F]', '', raw)
                try:
                    msgs.append(bytes.fromhex(raw_clean))
                except Exception:
                    continue
    return msgs

class RTP:
    def __init__(self, ip, port, bind_port=0, ssrc=None):
        self.ip = ip
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(('', bind_port))
        self.seq = 0
        self.ssrc = ssrc if ssrc is not None else 0x11223344

    def invite(self, name='BF'):
        token = 0x42424242
        sig=b'\xff\xff'; cmd=b'IN'; ver=struct.pack('!I', 2); tokenb=struct.pack('!I', token); ssrcb=struct.pack('!I', self.ssrc)
        pkt = sig + cmd + ver + tokenb + ssrcb + name.encode() + b'\x00'
        self.sock.sendto(pkt, (self.ip, self.port))
        try:
            self.sock.settimeout(1)
            data, addr = self.sock.recvfrom(1024)
            return data
        except socket.timeout:
            return None

    def send_sysex(self, syx):
        self.seq = (self.seq + 1) & 0xFFFF
        ts = int(time.time()*1000) & 0xFFFFFFFF
        rtp_hdr = struct.pack('!BBHII', 0x80, 0x61, self.seq, ts, self.ssrc)
        payload = b'\x00' + syx
        pkt = rtp_hdr + payload
        self.sock.sendto(pkt, (self.ip, self.port))

    def send_udp(self, data):
        self.sock.sendto(data, (self.ip, self.port))

    def close(self):
        try:
            self.sock.close()
        except Exception:
            pass


def find_short_08_msgs(msgs):
    out = []
    for m in msgs:
        if b'\x08\x7f\x7f' in m:
            out.append(m)
    return out


def reuse_invite_from_same_socket(rtp_client, port_check=PORT_CHECK):
    # craft an invite using same socket (reuse ssrc)
    token = 0x55555555
    sig=b'\xff\xff'; cmd=b'IN'; ver=struct.pack('!I', 2); tokenb=struct.pack('!I', token); ssrcb=struct.pack('!I', rtp_client.ssrc)
    pkt = sig + cmd + ver + tokenb + ssrcb + b'Reuse' + b'\x00'
    rtp_client.sock.sendto(pkt, (IP, port_check))
    try:
        rtp_client.sock.settimeout(1)
        data, addr = rtp_client.sock.recvfrom(1024)
        return data
    except socket.timeout:
        return None


def main():
    msgs = parse_msgs('firmware_sysex.txt')
    candidates = find_short_08_msgs(msgs)
    print('Total messages:', len(msgs), 'Short 08 msgs:', len(candidates))
    if not candidates:
        print('No candidates found')
        return

    # Replay first N messages across candidate sequence lengths
    for seq_len in [1, 3, 5, 10]:
        print('\nTesting sequence length:', seq_len)
        cseq = candidates[:seq_len]
        # establish RTP session to 5006 and send the sequence
        client = RTP(IP, PORT_SEND, bind_port=0)
        ok_resp = client.invite(name='ReplaySeq')
        print('Invite to 5006 response:', ok_resp)
        for m in cseq:
            client.send_sysex(m)
            time.sleep(0.05)
        # Now try invite to 5003 using same socket
        resp = reuse_invite_from_same_socket(client)
        print('Invite to 5003 via same socket resp:', resp)
        client.close()
        time.sleep(0.25)

if __name__ == '__main__':
    main()
