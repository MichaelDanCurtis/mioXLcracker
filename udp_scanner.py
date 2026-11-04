#!/usr/bin/env python3
"""
UDP port scanner for mioXL device
Since TCP scan found nothing, device must use UDP exclusively
"""

import socket
import struct
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed


def probe_udp_port(ip: str, port: int, timeout: float = 1.0) -> dict:
    """
    Probe UDP port with various packet types
    Returns info about the port if it responds
    """
    result = {
        'port': port,
        'responds': False,
        'response_type': None,
        'response_data': None
    }
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(timeout)
        
        # Try different probe packets
        probes = [
            # AppleMIDI invitation
            (b'\xff\xff' + b'IN' + struct.pack('!III', 2, 0x12345678, 0x87654321) + b'Probe\x00', 'AppleMIDI'),
            # Generic query
            (b'\x00\x01\x02\x03', 'Generic'),
            # Empty packet
            (b'', 'Empty'),
        ]
        
        for probe_data, probe_type in probes:
            try:
                sock.sendto(probe_data, (ip, port))
                
                # Wait for response
                try:
                    data, addr = sock.recvfrom(1024)
                    result['responds'] = True
                    result['response_type'] = probe_type
                    result['response_data'] = data
                    break
                except socket.timeout:
                    pass
            except:
                pass
        
        sock.close()
    except Exception as e:
        pass
    
    return result


def scan_udp_ports(ip: str):
    """Scan UDP ports on device"""
    print("\n" + "="*70)
    print(f"🔍 UDP Port Scanner: {ip}")
    print("="*70 + "\n")
    
    # UDP ports to check
    ports_to_scan = list(range(5000, 5020))

    
    print(f"📡 Probing {len(ports_to_scan)} UDP ports...")
    print("   (This may take a minute...)\n")
    
    responding_ports = []
    
    # Scan with limited concurrency (UDP can be unreliable with too many concurrent probes)
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(probe_udp_port, ip, port): port for port in ports_to_scan}
        
        for future in as_completed(futures):
            port = futures[future]
            try:
                result = future.result()
                if result['responds']:
                    responding_ports.append(result)
                    print(f"  ✓ Port {result['port']} responds to {result['response_type']} probe")
                    print(f"    Response: {result['response_data'][:32].hex()}")
            except Exception as e:
                pass
    
    print(f"\n{'='*70}")
    
    if responding_ports:
        print(f"✅ Found {len(responding_ports)} responding UDP port(s)")
        print(f"{'='*70}\n")
        
        for result in sorted(responding_ports, key=lambda x: x['port']):
            port = result['port']
            print(f"\n🔎 Port {port} Details:")
            print(f"   Probe type: {result['response_type']}")
            print(f"   Response length: {len(result['response_data'])} bytes")
            print(f"   Response hex: {result['response_data'].hex()}")
            
            # Try to decode response
            data = result['response_data']
            
            # Check for AppleMIDI
            if len(data) >= 4 and data[0:2] == b'\xff\xff':
                cmd = data[2:4].decode('ascii', errors='ignore')
                print(f"   Type: AppleMIDI {cmd} packet")
                
                if cmd == 'OK' and len(data) >= 16:
                    device_name = data[16:].decode('ascii', errors='ignore').rstrip('\x00')
                    print(f"   Device name: {device_name}")
            
            # Check for SysEx
            elif data[0] == 0xF0:
                print(f"   Type: SysEx message")
            
            # Check for text
            elif all(32 <= b < 127 or b in [9, 10, 13] for b in data[:min(20, len(data))]):
                try:
                    text = data.decode('ascii', errors='ignore')
                    print(f"   Text: {text[:100]}")
                except:
                    pass
    else:
        print(f"❌ No UDP ports responded")
        print(f"{'='*70}\n")
        print("💡 The device may:")
        print("   - Only accept packets from known/paired sources")
        print("   - Require a specific handshake sequence")
        print("   - Use a proprietary protocol we haven't probed")
    
    print("\n" + "="*70)
    print("📝 Next Steps:")
    print("="*70)
    print("\n1. Run network capture while using Auracle X:")
    print(f"     sudo python3 sniff_network.py {ip} 60")
    print("\n2. We already know port 5006 works with AppleMIDI")
    print("   Let's try sending different commands to it...")
    print()


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("\nUsage: python3 udp_scanner.py <device_ip>")
        print("\nExample:")
        print("  python3 udp_scanner.py 192.168.1.199")
        sys.exit(1)
    
    target_ip = sys.argv[1]
    scan_udp_ports(target_ip)


if __name__ == "__main__":
    main()
