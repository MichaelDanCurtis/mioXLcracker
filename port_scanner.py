#!/usr/bin/env python3
"""
Scan mioXL device for open ports and services
Discovers how Auracle X actually communicates with the device
"""

import socket
import sys
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed


def check_port(ip: str, port: int, timeout: float = 0.5) -> dict:
    """Check if a port is open"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((ip, port))
        sock.close()
        
        if result == 0:
            return {'port': port, 'open': True}
    except:
        pass
    
    return {'port': port, 'open': False}


def check_http_service(ip: str, port: int) -> dict:
    """Check if port serves HTTP/HTTPS"""
    info = {'http': False, 'https': False, 'content': None}
    
    # Try HTTP
    try:
        response = requests.get(f"http://{ip}:{port}", timeout=2, verify=False)
        info['http'] = True
        info['status'] = response.status_code
        info['headers'] = dict(response.headers)
        info['content'] = response.text[:500]
    except:
        pass
    
    # Try HTTPS
    if not info['http']:
        try:
            response = requests.get(f"https://{ip}:{port}", timeout=2, verify=False)
            info['https'] = True
            info['status'] = response.status_code
            info['headers'] = dict(response.headers)
            info['content'] = response.text[:500]
        except:
            pass
    
    return info


def scan_device(ip: str):
    """Comprehensive device scan"""
    print("\n" + "="*70)
    print(f"🔍 Scanning mioXL Device: {ip}")
    print("="*70 + "\n")
    
    # Common ports for various protocols
    ports_to_scan = [
        # Web/HTTP
        80, 443, 8080, 8443, 8000, 8888, 3000,
        # MIDI
        5004, 5005, 5006, 5007, 5008, 5009,
        # iConnectivity specific (guessed)
        21928, 21929, 49152, 49153, 49154,
        # Common services
        22, 23, 21, 139, 445, 548,
        # Websockets
        9000, 9001, 9002,
        # mDNS/Bonjour
        5353,
        # UPnP
        1900,
    ]
    
    print(f"📡 Scanning {len(ports_to_scan)} ports...")
    
    open_ports = []
    
    # Fast concurrent scan
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(check_port, ip, port) for port in ports_to_scan]
        
        for future in as_completed(futures):
            result = future.result()
            if result['open']:
                open_ports.append(result['port'])
                print(f"  ✓ Port {result['port']} is OPEN")
    
    if not open_ports:
        print("  ✗ No open ports found in scan range")
        return
    
    print(f"\n{'='*70}")
    print(f"✅ Found {len(open_ports)} open port(s)")
    print(f"{'='*70}\n")
    
    # Investigate each open port
    for port in sorted(open_ports):
        print(f"\n🔎 Investigating port {port}...")
        
        # Check if it's HTTP/HTTPS
        http_info = check_http_service(ip, port)
        
        if http_info['http'] or http_info['https']:
            protocol = "HTTPS" if http_info['https'] else "HTTP"
            print(f"   ✓ {protocol} service detected")
            print(f"   Status: {http_info.get('status', 'unknown')}")
            
            if http_info.get('headers'):
                print(f"   Headers:")
                for key, value in list(http_info['headers'].items())[:5]:
                    print(f"     {key}: {value}")
            
            if http_info.get('content'):
                print(f"   Content preview:")
                lines = http_info['content'].split('\n')[:5]
                for line in lines:
                    print(f"     {line[:70]}")
            
            # Try common API endpoints
            print(f"\n   Testing API endpoints:")
            test_endpoints = [
                '/api',
                '/api/device',
                '/api/presets',
                '/api/info',
                '/device',
                '/presets',
                '/config',
                '/status',
            ]
            
            protocol_prefix = "https" if http_info['https'] else "http"
            for endpoint in test_endpoints:
                try:
                    r = requests.get(f"{protocol_prefix}://{ip}:{port}{endpoint}", timeout=1, verify=False)
                    if r.status_code == 200:
                        print(f"     ✓ {endpoint}: {r.status_code} ({len(r.content)} bytes)")
                        if 'json' in r.headers.get('content-type', ''):
                            print(f"       JSON: {r.text[:100]}")
                    elif r.status_code != 404:
                        print(f"     • {endpoint}: {r.status_code}")
                except:
                    pass
        
        else:
            # Try to identify service by sending probe
            print(f"   • Non-HTTP service")
            
            # Check if it's RTP-MIDI
            if port in [5004, 5005, 5006, 5007]:
                print(f"   Type: Likely RTP-MIDI/AppleMIDI")
    
    print("\n" + "="*70)
    print("💡 Recommendations:")
    print("="*70)
    
    if any(p in open_ports for p in [80, 443, 8080, 8443]):
        print("\n✅ Device has HTTP/HTTPS interface!")
        print("   Auracle X likely uses REST API for configuration")
        print("   Run this to capture API calls:")
        print(f"     sudo python3 sniff_network.py {ip} 60")
    else:
        print("\n⚠ No HTTP interface found")
        print("   Device may use proprietary protocol over existing ports")
        print("   Run network capture while using Auracle X:")
        print(f"     sudo python3 sniff_network.py {ip} 60")
    
    print()


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("\nUsage: python3 port_scanner.py <device_ip>")
        print("\nExample:")
        print("  python3 port_scanner.py 192.168.1.199")
        sys.exit(1)
    
    target_ip = sys.argv[1]
    
    # Suppress SSL warnings
    import urllib3
    urllib3.disable_warnings()
    
    scan_device(target_ip)


if __name__ == "__main__":
    main()
