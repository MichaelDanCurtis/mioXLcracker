#!/usr/bin/env python3
"""
Decode firmware_reconstructed.bin using common 7-bit SysEx packing schemes and output candidate decoded files.
"""
from pathlib import Path

IN_FILE = 'firmware_reconstructed.bin'
OUT_A = 'firmware_decoded_schemeA.bin'
OUT_B = 'firmware_decoded_schemeB.bin'

b = Path(IN_FILE).read_bytes()
print('Input length', len(b))

# Scheme A: mask byte first, bits 0..6 correspond to next 7 bytes

def decode_scheme_a(data):
    out = bytearray()
    i = 0
    while i < len(data):
        block = data[i:i+8]
        if len(block) < 8:
            # append raw remainder
            out.extend(block)
            break
        mask = block[0]
        for j in range(1, 8):
            mbit = (mask >> (j-1)) & 1
            val = (mbit << 7) | block[j]
            out.append(val)
        i += 8
    return bytes(out)

# Scheme B: mask byte first, bits 7..1 correspond or reversed order

def decode_scheme_b(data):
    out = bytearray()
    i = 0
    while i < len(data):
        block = data[i:i+8]
        if len(block) < 8:
            out.extend(block)
            break
        mask = block[0]
        for j in range(1, 8):
            mbit = (mask >> (7-j)) & 1  # reversed mapping
            val = (mbit << 7) | block[j]
            out.append(val)
        i += 8
    return bytes(out)


outA = decode_scheme_a(b)
outB = decode_scheme_b(b)

Path(OUT_A).write_bytes(outA)
Path(OUT_B).write_bytes(outB)
print('Wrote', OUT_A, len(outA), 'bytes')
print('Wrote', OUT_B, len(outB), 'bytes')
