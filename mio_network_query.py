#!/usr/bin/env python3
"""
mio XL Network Query - Based on mioctl protocol implementation
Queries iConnectivity mio XL device over network using actual SysEx protocol
"""

import socket
import struct
import sys
import time
from enum import IntEnum, IntFlag


class cmdId(IntEnum):
    """Command IDs from mioctl"""
    SYS = 0x00
    DEVICE = 0x01
    INFO = 0x02
    PRESET = 0x03
    PHYSPORT = 0x04
    PORTINFO = 0x05
    MIDIPORT = 0x06


class cmdFl(IntFlag):
    """Command flags from mioctl"""
    VARARG = 0x01
    GET = 0x02
    SET = 0x10
    RESPONSE = 0x40
    QUERY = (GET | VARARG)


class infoId(IntEnum):
    """Information IDs from mioctl"""
    DEVICE_NAME = 0x01
    MANUFACTURER = 0x02
    SERIAL = 0x04
    FW_VERSION = 0x05
    HW_VERSION = 0x06
    NUM_PRESETS = 0x14


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


def decode7(bd):
    """Decode 7-bit format to value"""
    c = 0
    for v in bd[:]:
        c <<= 7
        c += v
    return c


def chksum(data):
    """Calculate checksum for SysEx message"""
    cs = 128 - (sum(data) % 128)
    if cs == 128:
        cs = 0
    return cs


def makearg(data):
    """Create argument block with length prefix"""
    arg = bytearray(data)
    arg.insert(0, len(arg) + 1)
    return arg


def makeSysex(devid, fooid, txnid, cmd):
    """
    Create SysEx message for mio device
    
    Structure:
    - Manufacturer ID: 0x00 0x01 0x73 (iConnectivity)
    - Message class: 0x7d
    - Device ID: 7 bytes
    - Unknown/foo ID: 6 bytes
    - Transaction ID: 2 bytes (7-bit encoded)
    - Command data
    - Checksum
    """
    mfid = bytearray((0x00, 0x01, 0x73))  # iConnectivity manufacturer ID
    msgcls = bytearray((0x7d,))
    
    body = fooid + encode7(txnid, 2) + cmd
    
    sysex = bytearray((0xF0,))  # SysEx start
    sysex += mfid + msgcls + devid + body
    sysex.append(chksum(body))
    sysex.append(0xF7)  # SysEx end
    
    return bytes(sysex)


def makeCommand(flags, cmd, args):
    """Create command message"""
    cmd_bytes = bytearray((flags, cmd, len(args)))
    for a in args:
        cmd_bytes.extend(a)
    
    clen = encode7(len(cmd_bytes), 2)
    return clen + cmd_bytes


def query_device_info(target_ip, target_port=5004):
    """
    Query device information using SysEx over network
    
    Args:
        target_ip: IP address of device
        target_port: UDP port (default 5004 for RTP-MIDI control)
    
    Returns:
        Device name string or None
    """
    print("=" * 70)
    print(f"Querying mio XL Device at {target_ip}:{target_port}")
    print("=" * 70)
    
    try:
        # Create UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(5)
        
        # Build device name query command (from mioctl getInfo)
        # arg1 = makearg((0x1, 0x1, infoId.DEVICE_NAME))
        arg1 = makearg(bytearray([0x1, 0x1, infoId.DEVICE_NAME]))
        
        # Create command
        cmd = makeCommand(cmdFl.QUERY, cmdId.INFO, [arg1])
        
        # Create SysEx message
        devid = bytearray(7)  # Broadcast to all devices
        fooid = bytearray(6)  # Unknown purpose
        txnid = 0x0001
        
        sysex = makeSysex(devid, fooid, txnid, cmd)
        
        print(f"\n→ Sending SysEx Query")
        print(f"   Command: INFO.GET (Device Name)")
        print(f"   Packet size: {len(sysex)} bytes")
        print(f"   Hex: {sysex.hex()}")
        
        # Send query
        sock.sendto(sysex, (target_ip, target_port))
        print(f"   ✓ Packet sent to {target_ip}:{target_port}")
        
        # Wait for response
        print(f"\n← Waiting for response (timeout: 5s)...")
        
        try:
            data, addr = sock.recvfrom(1024)
            
            print(f"   ✓ Received {len(data)} bytes from {addr[0]}:{addr[1]}")
            print(f"   Hex: {data.hex()}")
            
            # Parse SysEx response
            if len(data) >= 4 and data[0] == 0xF0:
                print(f"\n📦 Parsing SysEx Response:")
                
                # Check manufacturer ID
                mfid = data[1:4]
                if mfid == bytes([0x00, 0x01, 0x73]):
                    print(f"   ✓ Valid iConnectivity manufacturer ID")
                    
                    # Try to extract device name from response
                    # Response structure varies, look for ASCII string
                    for i in range(10, len(data) - 1):
                        if data[i] >= 0x20 and data[i] < 0x7F:
                            # Found potential ASCII string
                            name_start = i
                            name_end = name_start
                            
                            while name_end < len(data) - 1 and data[name_end] >= 0x20 and data[name_end] < 0x7F:
                                name_end += 1
                            
                            if name_end - name_start >= 3:
                                device_name = data[name_start:name_end].decode('ascii', errors='ignore')
                                print(f"\n{'=' * 70}")
                                print(f"🎹 DEVICE NAME: {device_name}")
                                print(f"{'=' * 70}")
                                
                                return {
                                    'name': device_name,
                                    'ip': target_ip,
                                    'port': target_port
                                }
                else:
                    print(f"   ✗ Unknown manufacturer ID: {mfid.hex()}")
            
            print(f"   ℹ Unable to parse device name from response")
            
        except socket.timeout:
            print(f"   ✗ No response received (timeout)")
            print(f"\n💡 Troubleshooting:")
            print(f"   - Verify device is powered on")
            print(f"   - Check network connectivity (ping {target_ip})")
            print(f"   - Ensure device has network MIDI enabled")
            print(f"   - Device may not support network SysEx queries")
            print(f"   - Try alternative ports (5005, 21928)")
        
        sock.close()
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    return None


def try_all_protocols(target_ip):
    """Try multiple protocols and ports to discover the device"""
    
    protocols = [
        ("RTP-MIDI Control (SysEx)", 5004, query_device_info),
        ("RTP-MIDI Data (SysEx)", 5005, query_device_info),
        ("iConnectivity Control", 21928, query_device_info),
    ]
    
    print(f"\n🔍 Attempting multi-protocol discovery for {target_ip}\n")
    
    for protocol_name, port, query_func in protocols:
        print(f"\n{'=' * 70}")
        print(f"Trying: {protocol_name} (Port {port})")
        print(f"{'=' * 70}")
        
        result = query_func(target_ip, port)
        
        if result:
            return result
        
        time.sleep(0.5)
    
    return None


def main():
    """Main entry point"""
    target_ip = sys.argv[1] if len(sys.argv) > 1 else "192.168.1.199"
    
    print("\n🎹 mio XL Network Query Tool (mioctl protocol)")
    print(f"Target: {target_ip}\n")
    
    result = try_all_protocols(target_ip)
    
    if result:
        print(f"\n\n✅ SUCCESS!")
        print(f"\nDevice Information:")
        print(f"  Name: {result['name']}")
        print(f"  IP: {result['ip']}")
        print(f"  Port: {result['port']}")
    else:
        print(f"\n\n❌ FAILED to identify device")
        print(f"\n💡 Alternative approaches:")
        print(f"   1. Connect via USB and use: python3 mio_xl_tester.py")
        print(f"   2. Use Auracle X to verify network MIDI is enabled")
        print(f"   3. Check device may require USB-first initialization")
    
    print("\n")


if __name__ == "__main__":
    main()
