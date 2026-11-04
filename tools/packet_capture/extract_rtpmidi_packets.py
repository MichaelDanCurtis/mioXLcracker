#!/usr/bin/env python3
"""
Parse a pcap file and extract UDP payloads for ports commonly used by RTP-MIDI/AppleMIDI
Usage:
    python3 extract_rtpmidi_packets.py capture.pcap

Requirements:
    pip3 install scapy

"""

import sys
from scapy.all import rdpcap, UDP

RTPMIDI_PORTS = {5003, 5004, 5005, 5006}


def hexdump(b: bytes) -> str:
    return b.hex()


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 extract_rtpmidi_packets.py <capture.pcap>")
        sys.exit(1)

    pcap_file = sys.argv[1]
    pkts = rdpcap(pcap_file)
    for i, pkt in enumerate(pkts):
        if UDP in pkt:
            sport = pkt[UDP].sport
            dport = pkt[UDP].dport
            if sport in RTPMIDI_PORTS or dport in RTPMIDI_PORTS:
                payload = bytes(pkt[UDP].payload)
                timestamp = pkt.time
                src = pkt[0].src if hasattr(pkt[0], 'src') else pkt[0].src
                dst = pkt[0].dst if hasattr(pkt[0], 'dst') else pkt[0].dst
                print(f"#{i} time={timestamp:.6f} {src}:{sport} -> {dst}:{dport} len={len(payload)}")
                if len(payload) > 0:
                    print(hexdump(payload))
                # Detect AppleMIDI control 'INVITE' (0xFF 0xFF 0x49 0x4E -> 'IN') and 'OK'/'NO'
                try:
                    if payload.startswith(b"\xff\xff") and len(payload) >= 4:
                        cmd = payload[2:4]
                        if cmd == b"IN":
                            print("-- AppleMIDI INVITE detected --\n")
                        elif cmd == b"OK":
                            print("-- AppleMIDI INVITE ACCEPTED (OK) detected --\n")
                        elif cmd == b"NO":
                            print("-- AppleMIDI INVITE REJECTED (NO) detected --\n")
                except Exception:
                    pass

if __name__ == '__main__':
    main()
