#!/usr/bin/env python3
"""
List messages from firmware where the payload data starts with 0x03 (flags byte) and extract command and args.
"""
from pathlib import Path
import re

DATA_FILE = 'firmware_sysex.txt'

def parse_hex(raw):
    return bytes.fromhex(re.sub('[^0-9a-fA-F]', '', raw))


def iter_raw():
    with open(DATA_FILE, 'r') as f:
        for line in f:
            if 'Raw:' in line:
                yield parse_hex(line.split('Raw:')[-1].strip())


def decode_txn(b1,b2):
    return (b1<<7) | b2


def try_decode(m):
    # Only parse SysEx messages matching our header
    if len(m) < 28:
        return None
    if m[0] != 0xF0:
        return None
    if m[1:4] != b'\x00\x01\x73':
        return None
    msgcls = m[4]
    devid = m[5:12]
    foo = m[12:24]
    txn = decode_txn(m[24], m[25])
    # parse clen
    pos = 26
    clen = m[pos]
    data_start = pos + 1
    if clen > len(m) - data_start - 2:
        # try 2-byte length
        if len(m) > pos+1:
            clen = (clen << 7) | m[pos+1]
            data_start = pos + 2
    data_bytes = m[data_start:data_start+clen] if clen > 0 else b''
    return {
        'msgcls': msgcls,
        'devid': devid,
        'txn': txn,
        'clen': clen,
        'cmd_bytes': data_bytes
    }

if __name__ == '__main__':
    found=0
    for i,m in enumerate(iter_raw()):
        x = try_decode(m)
        if not x:
            continue
        db = x['cmd_bytes']
        if len(db) >= 1 and db[0] == 0x03:
            print('Msg', i, 'len='+str(len(m)), 'txn='+str(x['txn']), 'devid='+x['devid'].hex(), 'cmd='+db.hex())
            found+=1
            if found >= 50:
                break
    print('Done - found', found)
