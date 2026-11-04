#!/usr/bin/env python3
"""
Identify AppleMIDI INVITE/OK/NO control packets in a pcap file and print details.

Usage: python3 identify_invite_messages.py capture.pcap

Dependencies: scapy

"""
import sys
from scapy.all import rdpcap, UDP
from parse_applemidi_control import parse as parse_apple


RTPMIDI_PORTS = {5003, 5004, 5005, 5006}


def hexdump(b: bytes) -> str:
    return ' '.join('{:02x}'.format(x) for x in b)


def read_invites(pcap_file):
    pkts = rdpcap(pcap_file)
    for i, pkt in enumerate(pkts):
        if UDP in pkt:
            sport = pkt[UDP].sport
            dport = pkt[UDP].dport
            if sport in RTPMIDI_PORTS or dport in RTPMIDI_PORTS:
                payload = bytes(pkt[UDP].payload)
                if len(payload) >= 4 and payload[:2] == b"\xff\xff":
                    cmd = payload[2:4].decode('ascii', errors='replace')
                    # Prefer IP addresses if present, otherwise show MAC
                    src = pkt[0].src
                    dst = pkt[0].dst
                    try:
                        src_ip = pkt['IP'].src
                        dst_ip = pkt['IP'].dst
                    except Exception:
                        src_ip = None
                        dst_ip = None
                    ts = pkt.time
                    if src_ip and dst_ip:
                        print(f"#{i} {ts:.6f} {src_ip}:{sport} -> {dst_ip}:{dport} CMD={cmd} len={len(payload)}")
                    else:
                        print(f"#{i} {ts:.6f} {src}:{sport} -> {dst}:{dport} CMD={cmd} len={len(payload)}")
                    print(hexdump(payload[:128]))
                    try:
                        print('\n-- Parsed fields --')
                        parse_apple(payload)
                        print('-- End parsed fields --\n')
                    except Exception as e:
                        print('parse error', e)
                    if len(payload) > 128:
                        print('... (truncated)')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python3 identify_invite_messages.py <capture.pcap>')
        sys.exit(1)
    read_invites(sys.argv[1])
