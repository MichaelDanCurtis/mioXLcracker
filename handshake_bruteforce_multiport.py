#!/usr/bin/env python3
"""
Brute-force across ports 5004/5005/5006 -> test unlocking 5003
- For each candidate short message in firmware
  - Send candidate via: (a) RTP session on port 5006, 5005, 5004 (b) Raw UDP to those ports
  - Try invite to 5003 after each attempt with multiple token/SSRC values
  - Log results
"""

import socket
import struct
import time
import threading
import random

IP = '192.168.1.199'
TARGET_INVITE = 5003
SRC_PORTS_TO_TEST = [5004, 5005, 5006]

RESULTS_FILE = 'handshake_multi_results.txt'


def load_short_messages(filename='firmware_sysex.txt', max_len=50):
    msgs = []
    with open(filename, 'r') as f:
        for line in f:
            if 'Raw:' in line:
                raw = line.split('Raw:')[-1].strip()
                try:
                    b = bytes.fromhex(raw)
                except Exception:
                    continue
                if len(b) <= max_len:
                    msgs.append(b)
    return msgs


class RTPClient:
    def __init__(self, ip, rport, local_port=0, ssrc=None):
        self.ip = ip
        self.rport = rport
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(('', local_port))
        self.sock.settimeout(0.5)
        self.seq = 0
        self.ssrc = ssrc if ssrc is not None else random.randint(1, 0xFFFFFFFF)

    def invite(self, token=None, name='X'):
        token = token if token is not None else random.randint(1, 0xFFFFFFFF)
        sig=b'\xff\xff'; cmd=b'IN'
        ver = struct.pack('!I', 2)
        tokenb = struct.pack('!I', token)
        ssrcb = struct.pack('!I', self.ssrc)
        pkt = sig + cmd + ver + tokenb + ssrcb + name.encode() + b'\x00'
        try:
            self.sock.sendto(pkt, (self.ip, self.rport))
            data, addr = self.sock.recvfrom(1024)
            return True, data
        except socket.timeout:
            return False, None

    def send_rtp_sysex(self, syx):
        self.seq = (self.seq + 1) & 0xFFFF
        ts = int(time.time()*1000) & 0xFFFFFFFF
        rtp = struct.pack('!BBHII', 0x80, 0x61, self.seq, ts, self.ssrc)
        payload = b'\x00' + syx
        pkt = rtp + payload
        self.sock.sendto(pkt, (self.ip, self.rport))

    def send_udp_raw(self, raw):
        self.sock.sendto(raw, (self.ip, self.rport))

    def close(self):
        try:
            self.sock.close()
        except Exception:
            pass


# Try inviting 5003 with various tokens/ssrcs

def try_invite_5003(source_port=0, ssrc=None, attempts=3):
    rc = []
    for i in range(attempts):
        client = RTPClient(IP, TARGET_INVITE, local_port=source_port, ssrc=ssrc)
        ok, resp = client.invite(name='Check')
        rc.append((ok, resp))
        client.close()
    return rc


def run_multi_bruteforce():
    candidates = load_short_messages()
    print(f'Loaded {len(candidates)} candidates')
    with open(RESULTS_FILE, 'w') as f:
        f.write(f'Multi port bruteforce: {IP}\nCandidates={len(candidates)}\n'
                f'Src ports: {SRC_PORTS_TO_TEST}\n')

    idx = 0
    for c in candidates:
        idx += 1
        print(f'Candidate {idx}/{len(candidates)} len={len(c)}')
        for src in SRC_PORTS_TO_TEST:
            # 1) Raw UDP to src
            client = RTPClient(IP, src, local_port=0)
            client.send_udp_raw(c)
            client.close()
            # give device time
            time.sleep(0.05)
            # Try invite 5003
            inv = try_invite_5003(source_port=0, ssrc=None, attempts=2)
            with open(RESULTS_FILE, 'a') as f:
                f.write(f'Cand {idx} len {len(c)} raw->port {src} invites: {inv}\n')
            # 2) RTP session -> send sysex via RTP
            client = RTPClient(IP, src, local_port=0)
            ok, resp = client.invite(name='multitest')
            if ok:
                client.send_rtp_sysex(c)
                time.sleep(0.05)
                inv2 = try_invite_5003(source_port=0, ssrc=None, attempts=2)
                with open(RESULTS_FILE, 'a') as f:
                    f.write(f'Cand {idx} len {len(c)} rtp->port {src} invites: {inv2}\n')
            else:
                with open(RESULTS_FILE, 'a') as f:
                    f.write(f'Cand {idx} rtp->port {src} invite failed to {src}: resp={resp}\n')
            client.close()
            time.sleep(0.05)
        # Also try re-sending candidate via 5006 multiple times and then try inviting 5003 from same source port
        client = RTPClient(IP, 5006, local_port=0)
        ok, resp = client.invite(name='multi-reuse')
        if ok:
            client.send_rtp_sysex(c)
            time.sleep(0.1)
            # Try invite from same local port used by client
            # Attempt an invite to 5003 using same socket (same source port) - avoids bind conflict
            try:
                sig=b'\xff\xff'; cmd=b'IN'; ver=struct.pack('!I', 2)
                token = random.randint(1, 0xFFFFFFFF)
                tokenb=struct.pack('!I', token)
                ssrcb=struct.pack('!I', client.ssrc)
                pkt = sig + cmd + ver + tokenb + ssrcb + b'Reuse' + b'\x00'
                client.sock.sendto(pkt, (IP, TARGET_INVITE))
                try:
                    data, addr = client.sock.recvfrom(1024)
                    inv_same = [(True, data)]
                except socket.timeout:
                    inv_same = [(False, None)]
            except Exception as e:
                inv_same = [(False, str(e))]
            with open(RESULTS_FILE, 'a') as f:
                f.write(f'Cand {idx} len {len(c)} rtp->5006 sameport invites: {inv_same}\n')
        client.close()
        # quick break if success found
        with open(RESULTS_FILE, 'r') as f:
            if 'True' in f.read():
                print('Found possible success (True in log) — stopping early')
                return
    print('Done')

if __name__ == '__main__':
    run_multi_bruteforce()
