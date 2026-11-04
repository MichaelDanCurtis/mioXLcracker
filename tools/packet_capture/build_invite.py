#!/usr/bin/env python3
"""
Build an AppleMIDI INVITE control packet from input fields.

Usage:
  python3 build_invite.py --ssrc <num> --token <num> --port <port> --name "MyName"

Then use replay tool to send the bytes:
  python3 tools/packet_capture/replay_hex_udp.py 192.168.1.7 5003 <hexpayload>

"""
import argparse
import struct
import random


def build_invite(ssrc=None, token=None, port=5006, name='pyClient'):
    if ssrc is None:
        ssrc = random.getrandbits(32)
    if token is None:
        token = random.getrandbits(32)
    # Header: 0xff 0xff + 'IN'
    payload = bytearray()
    payload.extend(b'\xff\xff')
    payload.extend(b'IN')
    # version word: 0x00010000 as heuristic
    payload.extend(struct.pack('>I', 0x00010000))
    # ssrc
    payload.extend(struct.pack('>I', ssrc))
    # token
    payload.extend(struct.pack('>I', token))
    # port (2 bytes big-endian) + padding
    payload.extend(struct.pack('>H', port))
    payload.extend(b'\x00\x00')
    # name (null-terminated)
    payload.extend(name.encode('utf-8'))
    payload.extend(b'\x00')
    return bytes(payload)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--ssrc', type=lambda x: int(x,0), help='SSRC (32-bit) int', default=None)
    parser.add_argument('--token', type=lambda x: int(x,0), help='initiator token (32-bit) int', default=None)
    parser.add_argument('--port', type=int, default=5006)
    parser.add_argument('--name', default='pyClient')
    args = parser.parse_args()

    payload = build_invite(ssrc=args.ssrc, token=args.token, port=args.port, name=args.name)
    print(payload.hex())
