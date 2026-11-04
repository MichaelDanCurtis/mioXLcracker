#!/usr/bin/env python3
"""
Network Device Discovery for mio XL
Attempts to identify and query mio XL device on the network
"""

import socket
import struct
import time
from typing import Optional, Dict


class NetworkDeviceDiscovery:
    """Discover and query network MIDI devices"""
    
    # RTP-MIDI (AppleMIDI) default ports
    RTPMIDI_CONTROL_PORT = 5004
    RTPMIDI_DATA_PORT = 5005
    
    # Bonjour/mDNS service types
    RTPMIDI_SERVICE = "_apple-midi._udp.local."
    
    def __init__(self, target_ip: str):
        """
        Initialize discovery for target IP.
        
        Args:
            target_ip: IP address of device
        """
        self.target_ip = target_ip
    
    def check_host_alive(self) -> bool:
        """Check if host responds"""
        print(f"\n=== Checking if {self.target_ip} is online ===")
        
        # Try to connect to common ports
        ports = [5004, 5005, 80, 8080, 443]
        
        for port in ports:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex((self.target_ip, port))
                sock.close()
                
                if result == 0:
                    print(f"✓ Port {port} is open")
                    return True
            except:
                pass
        
        print("✗ No response from device")
        return False
    
    def scan_ports(self) -> Dict[int, bool]:
        """Scan common ports"""
        print(f"\n=== Scanning Ports on {self.target_ip} ===")
        
        # Common ports for MIDI and web interfaces
        ports = [
            (80, "HTTP"),
            (443, "HTTPS"),
            (5004, "RTP-MIDI Control"),
            (5005, "RTP-MIDI Data"),
            (8080, "HTTP Alt"),
            (502, "Modbus TCP"),
            (21, "FTP"),
            (22, "SSH"),
            (23, "Telnet"),
        ]
        
        open_ports = {}
        
        for port, description in ports:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex((self.target_ip, port))
                sock.close()
                
                if result == 0:
                    print(f"✓ {port:5d} OPEN  - {description}")
                    open_ports[port] = True
                else:
                    print(f"  {port:5d} closed - {description}")
                    open_ports[port] = False
            except Exception as e:
                print(f"  {port:5d} error  - {description}: {e}")
                open_ports[port] = False
            
            time.sleep(0.1)
        
        return open_ports
    
    def probe_rtpmidi_session(self) -> Optional[Dict]:
        """
        Probe RTP-MIDI service for session information.
        
        This sends a session invitation to discover device name.
        """
        print(f"\n=== Probing RTP-MIDI Session ===")
        
        try:
            # Create UDP socket for RTP-MIDI control
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(3)
            
            # AppleMIDI Invitation command
            # Format: Signature (0xFFFF) + Command (IN) + Protocol Version + Initiator Token + SSRC + Name
            signature = b'\xff\xff'
            command = b'IN'  # Invitation
            protocol_version = struct.pack('!I', 2)  # Protocol version 2
            initiator_token = struct.pack('!I', 0x12345678)  # Random token
            ssrc = struct.pack('!I', 0x87654321)  # Random SSRC
            name = b'mioXLcracker\x00'  # Session name
            
            invitation = signature + command + protocol_version + initiator_token + ssrc + name
            
            print(f"→ Sending RTP-MIDI invitation to {self.target_ip}:{self.RTPMIDI_CONTROL_PORT}")
            sock.sendto(invitation, (self.target_ip, self.RTPMIDI_CONTROL_PORT))
            
            # Wait for response
            try:
                data, addr = sock.recvfrom(1024)
                print(f"← Received {len(data)} bytes from {addr}")
                print(f"   Data: {data.hex()}")
                
                # Parse response
                if len(data) >= 12 and data[0:2] == b'\xff\xff':
                    cmd = data[2:4].decode('ascii', errors='ignore')
                    print(f"   Command: {cmd}")
                    
                    if cmd == 'OK':
                        # Parse device name from response
                        if len(data) > 16:
                            device_name = data[16:].decode('ascii', errors='ignore').rstrip('\x00')
                            print(f"\n✓ Device Name: {device_name}")
                            return {
                                'name': device_name,
                                'ip': self.target_ip,
                                'port': self.RTPMIDI_CONTROL_PORT,
                                'protocol': 'RTP-MIDI'
                            }
                
            except socket.timeout:
                print("✗ No response to RTP-MIDI invitation")
            
            sock.close()
            
        except Exception as e:
            print(f"✗ RTP-MIDI probe failed: {e}")
        
        return None
    
    def try_http_request(self) -> Optional[str]:
        """Try to get device info via HTTP"""
        print(f"\n=== Trying HTTP Request ===")
        
        ports = [80, 8080, 443]
        
        for port in ports:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                
                if sock.connect_ex((self.target_ip, port)) == 0:
                    # Send HTTP GET request
                    request = f"GET / HTTP/1.1\r\nHost: {self.target_ip}\r\n\r\n"
                    sock.send(request.encode())
                    
                    response = sock.recv(4096).decode('utf-8', errors='ignore')
                    sock.close()
                    
                    # Look for device name in response
                    if 'mio' in response.lower() or 'iconnectivity' in response.lower():
                        print(f"✓ Found device info on port {port}")
                        print(f"Response preview:\n{response[:500]}")
                        return response
                    
            except Exception as e:
                pass
        
        print("✗ No HTTP response with device info")
        return None
    
    def discover(self) -> Dict:
        """Run full discovery process"""
        print("=" * 60)
        print(f"Network Device Discovery: {self.target_ip}")
        print("=" * 60)
        
        results = {
            'ip': self.target_ip,
            'alive': False,
            'open_ports': {},
            'device_info': None,
            'name': None
        }
        
        # Check if host is alive
        results['alive'] = self.check_host_alive()
        
        if not results['alive']:
            print("\n✗ Device is not responding")
            return results
        
        # Scan ports
        results['open_ports'] = self.scan_ports()
        
        # Try RTP-MIDI discovery
        device_info = self.probe_rtpmidi_session()
        if device_info:
            results['device_info'] = device_info
            results['name'] = device_info.get('name')
        
        # Try HTTP
        if not results['name']:
            http_response = self.try_http_request()
            if http_response:
                results['device_info'] = {'http_response': http_response}
        
        return results


def main():
    """Main discovery function"""
    import sys
    
    if len(sys.argv) > 1:
        target_ip = sys.argv[1]
    else:
        target_ip = "192.168.1.199"
    
    discovery = NetworkDeviceDiscovery(target_ip)
    results = discovery.discover()
    
    print("\n" + "=" * 60)
    print("DISCOVERY RESULTS")
    print("=" * 60)
    print(f"IP Address: {results['ip']}")
    print(f"Status: {'Online' if results['alive'] else 'Offline'}")
    
    if results['open_ports']:
        print(f"\nOpen Ports:")
        for port, is_open in results['open_ports'].items():
            if is_open:
                print(f"  - {port}")
    
    if results['name']:
        print(f"\n✓ DEVICE NAME: {results['name']}")
    else:
        print(f"\n✗ Could not determine device name")
    
    print("=" * 60)


if __name__ == "__main__":
    main()
