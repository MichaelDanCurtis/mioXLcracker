#!/usr/bin/env python3
"""
Extract the first AppleMIDI INVITE from a pcap and replay it to a target IP/port with optional source port.

Usage:
  python3 replay_invite_from_pcap.py <pcap> <target-ip> [<target-port>] [<source-port>]

"""
import sys
import socket
from scapy.all import rdpcap, UDP

RTPMIDI_PORTS = {5003, 5004, 5005, 5006}


def find_first_invite(pcap_path):
    pkts = rdpcap(pcap_path)
    for pkt in pkts:
        if UDP in pkt:
            payload = bytes(pkt[UDP].payload)
            if len(payload) >= 4 and payload[0] == 0xff and payload[1] == 0xff and payload[2:4] == b'IN':
                return payload
    return None


def main():
    if len(sys.argv) < 3:
        print('Usage: python3 replay_invite_from_pcap.py <pcap> <target-ip> [<target-port>] [<source-port>]')
        sys.exit(1)
    pcapfile = sys.argv[1]
    target = sys.argv[2]
    port = int(sys.argv[3]) if len(sys.argv) >= 4 else 5003
    local_port = int(sys.argv[4]) if len(sys.argv) >= 5 else None

    invite = find_first_invite(pcapfile)
    if invite is None:
        print('No INVITE found in pcap')
        sys.exit(1)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    if local_port:
        sock.bind(('0.0.0.0', local_port))
    sock.sendto(invite, (target, port))
    print(f'Replayed INVITE to {target}:{port} from source port {local_port if local_port else "random"}')

if __name__ == '__main__':
    main()
