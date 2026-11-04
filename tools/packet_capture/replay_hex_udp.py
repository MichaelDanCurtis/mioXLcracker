#!/usr/bin/env python3
"""
Replay a hex payload over UDP to specified IP and port.
Usage: python3 replay_hex_udp.py <host> <port> <hexpayload>
Example: python3 replay_hex_udp.py 192.168.1.123 5003 1f2e3d4c

"""
import sys
import socket


def hex_to_bytes(h):
    return bytes.fromhex(h)


def main():
    if len(sys.argv) < 4:
        print("Usage: python3 replay_hex_udp.py <host> <port> <hexpayload>")
        sys.exit(1)
    host = sys.argv[1]
    port = int(sys.argv[2])
    hexpayload = sys.argv[3]
    payload = hex_to_bytes(hexpayload)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(payload, (host, port))
    print(f"Sent {len(payload)} bytes to {host}:{port}")

if __name__ == '__main__':
    main()
