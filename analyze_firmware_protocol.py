#!/usr/bin/env python3
"""
Analyze parsed SysEx messages in firmware_sysex.txt to deduce protocol structure
and identify common command patterns (flags/cmd/nargs), device id patterns, and short commands.
"""
from pathlib import Path
from collections import Counter, defaultdict

DATA_FILE = 'firmware_sysex.txt'


def parse_hex_string(raw):
    import re
    s = re.sub(r'[^0-9a-fA-F]', '', raw)
    return bytes.fromhex(s)


def iter_raw_messages(file):
    with open(file, 'r') as f:
        for line in f:
            if 'Raw:' in line:
                raw = line.split('Raw:')[-1].strip()
                try:
                    yield parse_hex_string(raw)
                except Exception:
                    continue


def analyze():
    msgcls_counter = Counter()
    devid_counter = Counter()
    ticker = 0

    short_msgs = []

    flags_cmd_counter = Counter()
    first_data_buckets = Counter()

    txn_distribution = Counter()
    length_distribution = Counter()

    for m in iter_raw_messages(DATA_FILE):
        ticker += 1
        if len(m) < 6:
            continue
        if m[0] != 0xF0:
            continue
        # Basic header
        mfid = m[1:4]
        if mfid != bytes([0x00, 0x01, 0x73]):
            # skip unexpected manufacturer
            continue
        msgcls = m[4]
        msgcls_counter[msgcls] += 1
        if len(m) >= 12:
            devid = m[5:12]
            devid_counter[devid] += 1
        else:
            devid = b''
        # Body start
        if len(m) > 24:
            foo = m[12:24]
            # txn 2-byte 7-bit
            txn_b1, txn_b2 = m[24], m[25]
            txn_val = (txn_b1 << 7) | txn_b2
            txn_distribution[txn_val] += 1
            # length
            pos = 26
            # Try reading a variable length 7-bit encoded length (1 or 2 bytes)
            # We'll treat next byte as clen at pos
            # try 1-byte length first
            clen = m[pos]
            # if not enough bytes following but there is another byte, attempt 2-byte length
            remaining = len(m) - (pos + 1) - 1  # leaving space for checksum and F7
            if clen > remaining and (len(m) > pos + 2):
                # read 2-byte 7-bit encoded length
                clen_b1 = clen
                clen_b2 = m[pos+1]
                clen_val = (clen_b1 << 7) | clen_b2
                length_distribution[clen_val] += 1
                data_start = pos + 2
                clen = clen_val
            else:
                length_distribution[clen] += 1
                data_start = pos + 1
            # total length of body data
            length_distribution[clen] += 1
            # Post-clen data
            data_start = pos+1
            data_bytes = m[data_start: data_start + clen] if clen > 0 else b''
            if len(data_bytes) >= 3:
                flags= data_bytes[0]
                cmd = data_bytes[1]
                nargs = data_bytes[2] if len(data_bytes) > 2 else None
                flags_cmd_counter[(flags, cmd, nargs)] += 1
                first_data_buckets[data_bytes[:6]] += 1
        # Collect short messages for inspection
        if len(m) <= 48:
            short_msgs.append(m)

    # Print findings
    print(f'Total messages analyzed: {ticker}')
    print('\nMessage Class Counts:')
    for k,v in msgcls_counter.most_common():
        print(f'  msgcls 0x{k:02x}: {v}')

    print('\nTop 10 Device IDs:')
    for k,v in devid_counter.most_common(10):
        print('  {} : {}'.format(k.hex(), v))

    print('\nTxn distribution (sample):')
    for t,c in txn_distribution.most_common(10):
        print(f'  txn 0x{t:04x}: {c}')

    print('\nClen distribution sample:')
    for l in length_distribution.most_common(10):
        print(f'  len {l[0]} count {l[1]}')

    print('\nTop flag/cmd combos:')
    for (flags,cmd,nargs), count in flags_cmd_counter.most_common(20):
        nargs_str = f'0x{nargs:02x}' if nargs is not None else 'None'
        print(f'  flags=0x{flags:02x} cmd=0x{cmd:02x} nargs={nargs_str} count={count}')

    print('\nTop first-data patterns (first up to 6 bytes of payload):')
    for data, cnt in first_data_buckets.most_common(20):
        print(f'  {data.hex()} count={cnt}')

    # Print short messages unique patterns
    print('\nShort messages (len <=48) samples:')
    sample_count=0
    for m in short_msgs:
        if sample_count >= 30:
            break
        print(m.hex())
        sample_count += 1

    return {
        'msgcls': msgcls_counter,
        'devid': devid_counter,
        'txn': txn_distribution,
        'clen': length_distribution,
        'flags_cmd': flags_cmd_counter,
        'first_data': first_data_buckets,
        'short_msgs': short_msgs
    }

if __name__ == '__main__':
    analyze()
