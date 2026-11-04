#!/usr/bin/env python3
"""
Reconstruct raw firmware image from SysEx messages in firmware_sysex.txt.
- Expected to find many data block SysEx messages; concatenate the payload data into a binary.
- Save to firmware_reconstructed.bin
"""
import re
from pathlib import Path

IN_FILE = 'firmware_sysex.txt'
OUT_FILE = 'firmware_reconstructed.bin'

# Returns data chunks parsed from messages where payload length > threshold

def parse_and_concatenate(infile, min_data_len=16):
    with open(infile, 'r') as f:
        lines = f.readlines()

    out = bytearray()
    count=0
    for line in lines:
        if 'Raw:' not in line:
            continue
        raw = line.split('Raw:')[-1].strip()
        s = re.sub('[^0-9a-fA-F]', '', raw)
        if len(s) < 20:
            continue
        try:
            b = bytes.fromhex(s)
        except Exception:
            continue
        if not b.startswith(b'\xF0\x00\x01\x73'):
            continue
        # header layout: F0 00 01 73 msgclass devid(7) foo(12) txn(2) clen(1or2) payload...
        if len(b) < 28:
            continue
        # rely on message class 0x7d
        msgcls = b[4]
        if msgcls != 0x7d:
            continue
        # payload len at position 26
        pos = 26
        clen = b[pos]
        # try 2-byte length if necessary
        data_start = pos+1
        # check remaining bytes vs clen
        if clen > len(b) - data_start - 2 and len(b) > pos+1:
            clen = (clen << 7) | b[pos+1]
            data_start = pos+2
        payload = b[data_start:data_start+clen]
        if len(payload) >= min_data_len:
            out.extend(payload)
            count += 1

    with open(OUT_FILE, 'wb') as f:
        f.write(out)
    return OUT_FILE, count, len(out)

if __name__ == '__main__':
    ofname, cnt, outlen = parse_and_concatenate(IN_FILE)
    print(f'Wrote {ofname}: {cnt} blocks, {outlen} bytes')
