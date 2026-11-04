#!/usr/bin/env python3
"""
Simple heuristic parser for AppleMIDI control messages (INVITE/OK/NO/CK/RS/BY).
It won't be a full decoder, but will print the likely structure fields.

Usage:
  python3 parse_applemidi_control.py <hexpayload>

"""
import sys
import struct

def hexdump(b):
    return ' '.join('{:02x}'.format(x) for x in b)


def printable(b):
    return ''.join(chr(x) if 32 <= x <= 126 else '.' for x in b)


def parse(payload: bytes):
    if len(payload) < 4:
        print('payload too short')
        return
    if payload[0] == 0xff and payload[1] == 0xff:
        cmd = payload[2:4].decode('ascii', errors='replace')
        print('AppleMIDI ctrl cmd:', cmd)
    else:
        print('Not an AppleMIDI ctrl packet (no 0xff 0xff)')
        cmd = None
    print('len:', len(payload))
    print('raw hex:', hexdump(payload[:64]))
    # After the 4 bytes header, many implementations include 32-bit fields
    offset = 4
    # Print up to 4 32-bit fields if present
    for i in range(4):
        if offset + 4 <= len(payload):
            word = struct.unpack_from('>I', payload, offset)[0]
            print(f'word_{i}: 0x{word:08x} ({word})')
            offset += 4
        else:
            break
    # print any ASCII strings found in the remainder
    remaining = payload[offset:]
    if len(remaining) > 0:
        ascii_str = ''
        strings = []
        cur = []
        for ch in remaining:
            if 32 <= ch <= 126:
                cur.append(chr(ch))
            else:
                if len(cur) >= 3:
                    strings.append(''.join(cur))
                cur = []
        if len(cur) >= 3:
            strings.append(''.join(cur))
        if strings:
            print('Ascii strings in payload:', strings)
        else:
            print('No long ASCII strings in payload (first 64 bytes):', printable(remaining[:64]))


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python3 parse_applemidi_control.py <hexpayload>')
        sys.exit(1)
    hexp = sys.argv[1].replace(' ', '')
    try:
        payload = bytes.fromhex(hexp)
    except Exception as e:
        print('Invalid hex payload', e)
        sys.exit(1)
    parse(payload)
