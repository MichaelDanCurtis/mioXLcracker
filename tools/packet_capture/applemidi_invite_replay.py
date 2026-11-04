#!/usr/bin/env python3
"""
Send a raw AppleMIDI control packet payload to a target IP/port using a specific source port.

Usage:
  python3 applemidi_invite_replay.py <target-ip> <target-port> <hexpayload> [<local-source-port>]

Example:
  python3 applemidi_invite_replay.py 192.168.1.7 5003 ff ff 49 4e ... 5006

This helps to replicate the exact conditions of the original app: same source port, and payload.

"""
import sys
import socket
import argparse
from build_invite import build_invite


def hex_to_bytes(h: str) -> bytes:
    return bytes.fromhex(h.replace(' ', ''))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('host')
    parser.add_argument('port', type=int)
    parser.add_argument('hexpayload', nargs='?', help='hex payload or omit if using --build')
    parser.add_argument('--local-port', type=int, help='local source port to bind from')
    parser.add_argument('--build', action='store_true', help='build INVITE payload from params')
    parser.add_argument('--ssrc', type=lambda x: int(x,0), help='use with --build to provide ssrc (hex)')
    parser.add_argument('--token', type=lambda x: int(x,0), help='use with --build to provide token (hex)')
    parser.add_argument('--name', default='pyClient')
    parser.add_argument('--port-field', type=int, default=5006, help='rtp data port set in built invite (default 5006)')
    args = parser.parse_args()

    target_ip = args.host
    target_port = args.port
    hexpayload = args.hexpayload
    local_port = args.local_port
    if args.build:
        payload = build_invite(ssrc=args.ssrc, token=args.token, port=args.port_field, name=args.name)
        hexpayload = payload.hex()

    payload = hex_to_bytes(hexpayload)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    if local_port:
        sock.bind(("0.0.0.0", local_port))
    sock.sendto(payload, (target_ip, target_port))
    print(f"Sent {len(payload)} bytes to {target_ip}:{target_port} from source port {local_port if local_port else 'random'}")

if __name__ == '__main__':
    main()
