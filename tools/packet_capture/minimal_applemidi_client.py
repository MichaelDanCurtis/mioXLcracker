#!/usr/bin/env python3
"""
Minimal AppleMIDI client to send INVITE from a specific source port and wait for an OK reply.

Usage:
    python3 minimal_applemidi_client.py --target 192.168.1.199 --src-port 15005 --token 0xdeadbeef --ssrc 0x0000000b --name "localdomain [593]"

"""
import argparse
import random
import socket
import struct
import time


def build_invite(ssrc, token, name='pyClient'):
    """Build an AppleMIDI invitation packet."""
    payload = bytearray()
    payload.extend(b'\xff\xff')
    payload.extend(b'IN')
    # Protocol version (always 2 for AppleMIDI)
    payload.extend(struct.pack('>I', 0x00000002))
    # SSRC (synchronization source identifier)
    payload.extend(struct.pack('>I', ssrc))
    # Initiator token (unique per attempt)
    payload.extend(struct.pack('>I', token))
    # Session name (null-terminated)
    payload.extend(name.encode('utf-8'))
    payload.extend(b'\x00')
    return bytes(payload)


def parse_cmd(payload: bytes):
    if len(payload) < 4:
        return None
    if payload[0] == 0xff and payload[1] == 0xff:
        return payload[2:4].decode('ascii', errors='replace')
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--target', required=True)
    parser.add_argument('--control-port', type=int, default=5003)
    parser.add_argument('--src-port', type=int, required=True)
    parser.add_argument('--token', type=lambda x: int(x,0), default=None)
    parser.add_argument('--ssrc', type=lambda x: int(x,0), required=True)
    parser.add_argument('--name', default='pyClient')
    parser.add_argument('--timeout', type=float, default=5.0)
    args = parser.parse_args()

    token = args.token if args.token is not None else random.getrandbits(32)
    payload = build_invite(ssrc=args.ssrc, token=token, name=args.name)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('0.0.0.0', args.src_port))
    sock.settimeout(args.timeout)
    print(
        f"Sending INVITE to {args.target}:{args.control_port} from source port {args.src_port} "
        f"(token=0x{token:08x}, ssrc=0x{args.ssrc:08x})"
    )
    sock.sendto(payload, (args.target, args.control_port))
    start = time.time()
    try:
        while True:
            data, addr = sock.recvfrom(2048)
            cmd = parse_cmd(data)
            print('Received cmd:', cmd, 'from', addr, 'len', len(data))
            if cmd == 'OK':
                print('Device accepted INVITE!')
                break
            if time.time() - start > args.timeout:
                print('Timeout waiting for OK')
                break
    except socket.timeout:
        print('Socket timed out waiting for reply')


if __name__ == '__main__':
    main()
