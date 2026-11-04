#!/usr/bin/env python3
"""
Find specific control patterns inside the extracted SysEx messages.
"""
from pathlib import Path
import re

DATA_FILE = 'firmware_sysex.txt'
PATTERNS = [
    bytes.fromhex('03 03 02'),
    bytes.fromhex('03 02'),
    bytes.fromhex('03 03 02 05 04 01'),
    bytes.fromhex('03 03 02 05 04 01 09'),
    bytes.fromhex('08 7F 7F'),
]


def iter_raw_messages(file):
    with open(file, 'r') as f:
        for line in f:
            if 'Raw:' in line:
                raw = line.split('Raw:')[-1].strip()
                s = re.sub('[^0-9a-fA-F]', '', raw)
                try:
                    yield bytes.fromhex(s)
                except Exception:
                    continue


def find():
    messages = list(iter_raw_messages(DATA_FILE))
    print('Total messages:', len(messages))
    for p in PATTERNS:
        found = 0
        print('\nSearching for pattern', p.hex())
        for i,m in enumerate(messages):
            if p in m:
                found += 1
                print('  Msg idx', i, 'len', len(m), 'm snippet:', m.hex()[:120])
                if found >= 10:
                    break
        print('Found', found, 'occurrences (showing up to 10)')

if __name__ == '__main__':
    find()
