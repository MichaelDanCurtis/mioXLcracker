#!/usr/bin/env python3
"""
Brute-force handshake checker:
- For each candidate short SysEx message from firmware_sysex.txt
  1) Start RTP-MIDI session to port 5006, keep alive.
  2) Send candidate via RTP encapsulation (send_sysex)
  3) Attempt to invite to port 5003 from ephemeral port, then try reusing same local port.
  4) Optionally try modified message (000E -> 0000 or vice versa)
  5) Record any successes (invitation OK) to results file.

This script requires that the host is reachable and that port 5006 accepts AppleMIDI invitations.
"""

import socket
import struct
import threading
import time
import sys

IP = sys.argv[1] if len(sys.argv) > 1 else "192.168.1.199"
PORT6 = 5006
PORT3 = 5003

RESULTS_FILE = "handshake_results.txt"


# Load short messages from firmware_sysex.txt

def load_short_messages(filename, max_len=50):
    msgs = []
    with open(filename, 'r') as f:
        for line in f:
            if "Raw:" in line:
                raw = line.split("Raw:")[-1].strip()
                try:
                    b = bytes.fromhex(raw)
                except Exception:
                    continue
                if len(b) <= max_len:
                    msgs.append(b)
    return msgs


class RTPAppleMIDI:
    def __init__(self, ip, port, bind_port=0):
        self.ip = ip
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(('', bind_port))
        self.sock.settimeout(0.5)
        self.seq = 0
        self.ssrc = 0x11223344
        self.keep_running = False
        self.keep_thread = None

    def invite(self, name='BFTEST'):
        token = 0x41424344
        sig = b"\xff\xff"
        cmd = b"IN"
        ver = struct.pack("!I", 2)
        tokenb = struct.pack("!I", token)
        ssrcb = struct.pack("!I", self.ssrc)
        pkt = sig + cmd + ver + tokenb + ssrcb + name.encode() + b"\x00"
        try:
            self.sock.sendto(pkt, (self.ip, self.port))
            data, addr = self.sock.recvfrom(1024)
            if data[0:2] == b"\xff\xff" and data[2:4] == b"OK":
                return True, data
            else:
                return False, data
        except socket.timeout:
            return False, None

    def send_sysex(self, syx):
        self.seq = (self.seq + 1) & 0xFFFF
        timestamp = int(time.time()*1000) & 0xFFFFFFFF
        rtp_hdr = struct.pack("!BBHII", 0x80, 0x61, self.seq, timestamp, self.ssrc)
        midi_flags = b"\x00"
        packet = rtp_hdr + midi_flags + syx
        self.sock.sendto(packet, (self.ip, self.port))

    def keep_alive(self):
        self.keep_running = True
        while self.keep_running:
            try:
                pkt = bytes.fromhex("ffff434b0000000b0000000000000000000767f000000000000000000000000000000000")
                self.sock.sendto(pkt, (self.ip, self.port))
            except Exception:
                pass
            time.sleep(3)

    def start_keepalive(self):
        if self.keep_thread is None:
            self.keep_thread = threading.Thread(target=self.keep_alive, daemon=True)
            self.keep_thread.start()

    def stop(self):
        self.keep_running = False
        try:
            self.sock.close()
        except Exception:
            pass


def attempt_variant_and_invites(candidate, ip=IP, port6=PORT6, port3=PORT3):
    results = []
    # We'll test 3 variants: raw, mod (0x0E->0x00), mod reverse (0x00->0x0E) if present.
    variants = [candidate]
    if len(candidate) > 7:
        if candidate[6] == 0x0E:
            mod = bytearray(candidate); mod[6] = 0x00; variants.append(bytes(mod))
        elif candidate[6] == 0x00:
            mod = bytearray(candidate); mod[6] = 0x0E; variants.append(bytes(mod))
    # Also try toggling first 'payload' byte after header if present (e.g., 0x08 -> 0x09)
    if len(candidate) > 22:
        v2 = bytearray(candidate); v2[22] = (v2[22] + 1) & 0x7F; variants.append(bytes(v2))

    for v in variants:
        # 1. Start session on port 6
        sess6 = RTPAppleMIDI(ip, port6)
        ok, data = sess6.invite()
        if not ok:
            sess6.stop(); continue
        # Keep alive
        sess6.start_keepalive()
        time.sleep(0.1)
        # 2. Send candidate via RTP
        sess6.send_sysex(v)
        time.sleep(0.2)
        # 3. Try to invite port 3 from ephemeral port
        sess3 = RTPAppleMIDI(ip, port3)
        ok3, resp3 = sess3.invite()
        results.append((v, 'new', ok3, resp3))
        sess3.stop()
        if ok3:
            sess6.stop(); return results
        # 4. Try to invite to port 3 using same source port as sess6
        try:
            saved_port = sess6.sock.getsockname()[1]
            sess6.stop()
            # Re-create socket bound to same source port and invite to 5003
            sess3_same = RTPAppleMIDI(ip, port3, bind_port=saved_port)
            ok3b, resp3b = sess3_same.invite()
            results.append((v, 'sameport', ok3b, resp3b))
            sess3_same.stop()
            if ok3b:
                return results
        except Exception as e:
            results.append((v, 'sameport', False, str(e)))
            pass
        # cleanup
        sess6.stop()
        time.sleep(0.05)
    return results


def run_bruteforce():
    candidates = load_short_messages('firmware_sysex.txt', max_len=50)
    print(f"Loaded {len(candidates)} short candidates")

    with open(RESULTS_FILE, 'w') as out:
        out.write(f"Bruteforce run: target {IP}\nCandidates: {len(candidates)}\n\n")

    idx = 0
    for c in candidates:
        idx += 1
        print(f"Testing candidate {idx}/{len(candidates)} length={len(c)}")
        try:
            res = attempt_variant_and_invites(c)
            # Write results
            with open(RESULTS_FILE, 'a') as out:
                out.write(f"Candidate {idx} len={len(c)}:\n")
                for r in res:
                    vhex = r[0].hex()
                    out.write(f"  Variant({r[1]}): ok={r[2]} resp={r[3]} data={vhex}\n")
                out.write('\n')
            # If successful, print and exit early
            if any(r[2] for r in res):
                print("=== SUCCESS: Some variant opened port 5003! ===")
                for r in res:
                    if r[2]:
                        print(f"Success variant: type={r[1]} resp={r[3]} data={r[0].hex()}")
                break
        except KeyboardInterrupt:
            print('User canceled')
            break
        except Exception as e:
            print(f"Exception on candidate {idx}: {e}")
        time.sleep(0.05)

    print('Done')


if __name__ == '__main__':
    run_bruteforce()
