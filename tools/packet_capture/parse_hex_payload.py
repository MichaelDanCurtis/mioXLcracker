#!/usr/bin/env python3
"""
A tiny helper to print details of a hex payload for AppleMIDI/RT-PMIDI control packets.
Helps to inspect header bytes and ASCII.

Usage:
  python3 parse_hex_payload.py <hexpayload>

"""
import sys


def hexdump(bytes_):
    out = []
    for i, b in enumerate(bytes_):
        out.append(f"{b:02x}")
    return ' '.join(out)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 parse_hex_payload.py <hexpayload>")
        sys.exit(1)
    payload = bytes.fromhex(sys.argv[1])
    print('len:', len(payload))
    print('hex:', hexdump(payload[:64]))
    try:
        ascii_part = ''.join(chr(b) if 32 <= b <= 127 else '.' for b in payload[:64])
        print('ascii:', ascii_part)
    except Exception:
        pass

