#!/usr/bin/env python3
"""
Query mioXL presets via RTP-MIDI with embedded SysEx
Based on mioctl protocol - sends SysEx through RTP-MIDI session
"""

import socket
import struct
import sys
import time


def encode7(val, size=2):
    """Encode value into 7-bit format"""
    bd = bytearray()
    while val > 0:
        c = val & 0x7f
        val >>= 7
        bd.insert(0, c)
    while len(bd) < size:
        bd.insert(0, 0x00)
    return bd


def chksum(data):
    """Calculate SysEx checksum"""
    cs = 128 - (sum(data) % 128)
    if cs == 128:
        cs = 0
    return cs


def makearg(data):
    """Create argument with length prefix"""
    arg = bytearray(data)
    arg.insert(0, len(arg) + 1)
    return arg


def make_preset_query_sysex(txn_id=1):
    """
    Create SysEx to query current preset number
    Based on mioctl: arg1 = makearg((0x1, 0x1, 0x1))
    Command: PRESET, Flags: QUERY, Info: current preset
    """
    mfid = bytearray((0x00, 0x01, 0x73))  # iConnectivity
    msgcls = bytearray((0x7d,))
    devid = bytearray(7)  # Broadcast
    fooid = bytearray(6)
    
    # Build command: QUERY PRESET get current
    flags = 0x03  # QUERY (GET | VARARG)
    cmd = 0x03    # PRESET
    nargs = 0x01
    arg1 = makearg(bytearray([0x01, 0x01, 0x01]))  # Query current preset
    
    cmd_data = bytearray([flags, cmd, nargs]) + arg1
    clen = encode7(len(cmd_data), 2)
    body = fooid + encode7(txn_id, 2) + clen + cmd_data
    
    sysex = bytearray([0xF0]) + mfid + msgcls + devid + body
    sysex.append(chksum(body))
    sysex.append(0xF7)
    
    return bytes(sysex)


def make_preset_name_query_sysex(preset_num, txn_id=1):
    """
    Create SysEx to query preset name
    Based on mioctl: 
      arg1 = makearg((0x4, 0x1, 0x9, preset_num))
      arg2 = makearg((0x1, 0x1, 0x2))
    """
    mfid = bytearray((0x00, 0x01, 0x73))
    msgcls = bytearray((0x7d,))
    devid = bytearray(7)
    fooid = bytearray(6)
    
    flags = 0x03  # QUERY
    cmd = 0x03    # PRESET
    nargs = 0x02
    arg1 = makearg(bytearray([0x04, 0x01, 0x09, preset_num]))
    arg2 = makearg(bytearray([0x01, 0x01, 0x02]))
    
    cmd_data = bytearray([flags, cmd, nargs]) + arg1 + arg2
    clen = encode7(len(cmd_data), 2)
    body = fooid + encode7(txn_id, 2) + clen + cmd_data
    
    sysex = bytearray([0xF0]) + mfid + msgcls + devid + body
    sysex.append(chksum(body))
    sysex.append(0xF7)
    
    return bytes(sysex)


def make_num_presets_query_sysex(txn_id=1):
    """
    Query number of presets
    Command: INFO, Info ID: NUM_PRESETS (0x14)
    """
    mfid = bytearray((0x00, 0x01, 0x73))
    msgcls = bytearray((0x7d,))
    devid = bytearray(7)
    fooid = bytearray(6)
    
    flags = 0x03  # QUERY
    cmd = 0x02    # INFO
    nargs = 0x01
    arg1 = makearg(bytearray([0x01, 0x01, 0x14]))  # NUM_PRESETS
    
    cmd_data = bytearray([flags, cmd, nargs]) + arg1
    clen = encode7(len(cmd_data), 2)
    body = fooid + encode7(txn_id, 2) + clen + cmd_data
    
    sysex = bytearray([0xF0]) + mfid + msgcls + devid + body
    sysex.append(chksum(body))
    sysex.append(0xF7)
    
    return bytes(sysex)


def send_sysex_via_rtpmidi(ip, port, sysex_data):
    """Send SysEx embedded in RTP-MIDI packet"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(5)
    
    # First establish session
    signature = b'\xff\xff'
    command = b'IN'
    protocol_version = struct.pack('!I', 2)
    initiator_token = struct.pack('!I', 0x12345678)
    ssrc = struct.pack('!I', 0x87654321)
    name_bytes = b'PresetQuery\x00'
    
    invitation = signature + command + protocol_version + initiator_token + ssrc + name_bytes
    sock.sendto(invitation, (ip, port))
    
    # Wait for acceptance
    try:
        data, addr = sock.recvfrom(1024)
        if data[2:4] != b'OK':
            print(f"  ✗ Session not accepted on port {port}")
            sock.close()
            return None
    except socket.timeout:
        print(f"  ✗ No response from port {port}")
        sock.close()
        return None
    
    print(f"  ✓ Session established on port {port}")
    
    # Now send SysEx in RTP-MIDI packet
    # RTP header
    vpxcc = 0x80
    mpt = 0x61
    sequence = 1
    timestamp = int(time.time() * 1000) & 0xFFFFFFFF
    ssrc_rtp = 0x87654321
    
    rtp_header = struct.pack('!BBHII', vpxcc, mpt, sequence, timestamp, ssrc_rtp)
    
    # MIDI payload with SysEx
    midi_flags = 0x00
    midi_payload = bytes([midi_flags]) + sysex_data
    
    packet = rtp_header + midi_payload
    
    print(f"  → Sending SysEx query ({len(sysex_data)} bytes)")
    print(f"     {sysex_data.hex()}")
    
    sock.sendto(packet, (ip, port))
    
    # Listen for response
    print(f"  ← Waiting for response...")
    responses = []
    
    start_time = time.time()
    while time.time() - start_time < 3:
        try:
            sock.settimeout(0.5)
            data, addr = sock.recvfrom(2048)
            responses.append(data)
            print(f"     Received {len(data)} bytes: {data[:32].hex()}...")
        except socket.timeout:
            break
    
    sock.close()
    return responses


def query_all_presets(ip, port=5006):
    """Query all presets from device"""
    print("\n" + "="*70)
    print(f"🎹 Querying Presets from {ip}:{port}")
    print("="*70 + "\n")
    
    # Query number of presets
    print("1. Querying number of presets...")
    sysex = make_num_presets_query_sysex(txn_id=1)
    responses = send_sysex_via_rtpmidi(ip, port, sysex)
    
    if responses:
        print(f"\n   Got {len(responses)} response(s)")
        for r in responses:
            print(f"   {r.hex()}")
    
    time.sleep(0.5)
    
    # Query current preset
    print("\n2. Querying current preset...")
    sysex = make_preset_query_sysex(txn_id=2)
    responses = send_sysex_via_rtpmidi(ip, port, sysex)
    
    if responses:
        print(f"\n   Got {len(responses)} response(s)")
        for r in responses:
            print(f"   {r.hex()}")
    
    time.sleep(0.5)
    
    # Try querying preset names 1-10
    print("\n3. Querying preset names (1-10)...")
    preset_names = {}
    
    for preset_num in range(1, 11):
        print(f"\n   Preset {preset_num}:")
        sysex = make_preset_name_query_sysex(preset_num, txn_id=10+preset_num)
        responses = send_sysex_via_rtpmidi(ip, port, sysex)
        
        if responses:
            for r in responses:
                # Try to extract text from response
                if len(r) > 20:
                    # Look for ASCII text
                    for i in range(20, len(r)):
                        if r[i] >= 0x20 and r[i] < 0x7F:
                            end = i
                            while end < len(r) and r[end] >= 0x20 and r[end] < 0x7F:
                                end += 1
                            if end - i > 2:
                                text = r[i:end].decode('ascii', errors='ignore')
                                preset_names[preset_num] = text
                                print(f"      Name: {text}")
                                break
        
        time.sleep(0.3)
    
    print("\n" + "="*70)
    print("📋 PRESET SUMMARY")
    print("="*70 + "\n")
    
    if preset_names:
        for num in sorted(preset_names.keys()):
            print(f"  {num}. {preset_names[num]}")
    else:
        print("  ⚠ No preset names extracted from responses")
        print("  The device may:")
        print("    - Require USB connection for SysEx config queries")
        print("    - Use a different protocol for network configuration")
        print("    - Need authentication or pairing first")
    
    print()


if __name__ == "__main__":
    ip = sys.argv[1] if len(sys.argv) > 1 else "192.168.1.199"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 5006
    
    query_all_presets(ip, port)
