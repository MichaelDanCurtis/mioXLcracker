#!/usr/bin/env python3
"""
UDP-Based mio XL Device Discovery
Discovers and identifies iConnectivity devices using network protocols
"""

import socket
import struct
import sys
import time
import select
from dataclasses import dataclass
from typing import Optional, List


@dataclass
class MioDevice:
    """Discovered mio device information"""
    ip: str
    port: int
    name: str
    protocol: str
    ssrc: Optional[int] = None
    token: Optional[int] = None


class UDPDeviceDiscovery:
    """UDP-based device discovery for mio XL"""
    
    def __init__(self, timeout: float = 2.0):
        self.timeout = timeout
        self.devices: List[MioDevice] = []
    
    def send_applemidi_invitation(self, target_ip: str, port: int = 5004, session_name: str = "Discovery") -> Optional[MioDevice]:
        """
        Send AppleMIDI session invitation and parse device response
        
        Args:
            target_ip: IP address to query
            port: UDP port (5004 for control, 5005 for data)
            session_name: Session identifier
            
        Returns:
            MioDevice if successful, None otherwise
        """
        print(f"→ Trying AppleMIDI on {target_ip}:{port}")
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(self.timeout)
            
            # Build AppleMIDI Invitation packet
            # Format: signature(2) + cmd(2) + version(4) + token(4) + ssrc(4) + name(var)
            signature = b'\xff\xff'
            command = b'IN'
            protocol_version = struct.pack('!I', 2)
            initiator_token = struct.pack('!I', 0x12345678)
            ssrc = struct.pack('!I', 0x87654321)
            name_bytes = session_name.encode('ascii') + b'\x00'
            
            packet = signature + command + protocol_version + initiator_token + ssrc + name_bytes
            
            # Send invitation
            sock.sendto(packet, (target_ip, port))
            
            # Wait for response
            try:
                data, addr = sock.recvfrom(1024)
                
                if len(data) >= 4:
                    response_sig = data[0:2]
                    response_cmd = data[2:4]
                    
                    if response_sig == b'\xff\xff':
                        cmd_str = response_cmd.decode('ascii', errors='ignore')
                        
                        if cmd_str == 'OK' and len(data) >= 16:
                            # Parse acceptance response
                            proto_ver = struct.unpack('!I', data[4:8])[0]
                            resp_token = struct.unpack('!I', data[8:12])[0]
                            resp_ssrc = struct.unpack('!I', data[12:16])[0]
                            
                            # Extract device name
                            device_name = "Unknown"
                            if len(data) > 16:
                                device_name = data[16:].decode('ascii', errors='ignore').rstrip('\x00')
                            
                            print(f"  ✓ Device responded: {device_name}")
                            
                            device = MioDevice(
                                ip=target_ip,
                                port=port,
                                name=device_name,
                                protocol="AppleMIDI",
                                ssrc=resp_ssrc,
                                token=resp_token
                            )
                            
                            return device
                        
                        elif cmd_str == 'NO':
                            print(f"  ✗ Invitation rejected")
                            return None
                            
            except socket.timeout:
                pass
            
            sock.close()
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
        
        return None
    
    def send_mdns_query(self, target_ip: str = "224.0.0.251", port: int = 5353) -> List[MioDevice]:
        """
        Send mDNS query for _apple-midi._udp.local services
        
        Args:
            target_ip: mDNS multicast address
            port: mDNS port (5353)
            
        Returns:
            List of discovered devices
        """
        print(f"→ Trying mDNS query on {target_ip}:{port}")
        
        try:
            # Build mDNS query for _apple-midi._udp.local
            transaction_id = b'\x00\x00'
            flags = b'\x00\x00'  # Standard query
            questions = b'\x00\x01'  # 1 question
            answer_rrs = b'\x00\x00'
            authority_rrs = b'\x00\x00'
            additional_rrs = b'\x00\x00'
            
            # Query name: _apple-midi._udp.local
            qname = b'\x0b_apple-midi\x04_udp\x05local\x00'
            qtype = b'\x00\x0c'  # PTR
            qclass = b'\x00\x01'  # IN
            
            query = transaction_id + flags + questions + answer_rrs + authority_rrs + additional_rrs
            query += qname + qtype + qclass
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(self.timeout)
            
            sock.sendto(query, (target_ip, port))
            
            # Collect responses
            devices = []
            start_time = time.time()
            
            while time.time() - start_time < self.timeout:
                try:
                    data, addr = sock.recvfrom(2048)
                    # Parse mDNS response (simplified)
                    # Real parsing would decode DNS packet format
                    print(f"  ✓ mDNS response from {addr[0]} ({len(data)} bytes)")
                    
                except socket.timeout:
                    break
            
            sock.close()
            return devices
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
        
        return []
    
    def send_broadcast_discovery(self, broadcast_ip: str = "255.255.255.255", port: int = 5004) -> List[MioDevice]:
        """
        Send broadcast discovery packets
        
        Args:
            broadcast_ip: Broadcast address
            port: Target port
            
        Returns:
            List of discovered devices
        """
        print(f"→ Trying broadcast discovery on {broadcast_ip}:{port}")
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.settimeout(self.timeout)
            
            # Send AppleMIDI invitation as broadcast
            signature = b'\xff\xff'
            command = b'IN'
            protocol_version = struct.pack('!I', 2)
            initiator_token = struct.pack('!I', 0xBBBBBBBB)
            ssrc = struct.pack('!I', 0xAAAAAAAA)
            name_bytes = b'Broadcast\x00'
            
            packet = signature + command + protocol_version + initiator_token + ssrc + name_bytes
            
            sock.sendto(packet, (broadcast_ip, port))
            
            # Collect responses
            devices = []
            start_time = time.time()
            
            while time.time() - start_time < self.timeout:
                try:
                    data, addr = sock.recvfrom(1024)
                    
                    if len(data) >= 16 and data[0:2] == b'\xff\xff':
                        cmd = data[2:4].decode('ascii', errors='ignore')
                        if cmd == 'OK':
                            device_name = data[16:].decode('ascii', errors='ignore').rstrip('\x00')
                            print(f"  ✓ Device found at {addr[0]}: {device_name}")
                            
                            device = MioDevice(
                                ip=addr[0],
                                port=port,
                                name=device_name,
                                protocol="AppleMIDI-Broadcast"
                            )
                            devices.append(device)
                    
                except socket.timeout:
                    break
            
            sock.close()
            return devices
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
        
        return []
    
    def scan_subnet(self, base_ip: str, start: int = 1, end: int = 254) -> List[MioDevice]:
        """
        Scan subnet for mio devices
        
        Args:
            base_ip: Base IP (e.g., "192.168.1")
            start: Start host number
            end: End host number
            
        Returns:
            List of discovered devices
        """
        print(f"\n→ Scanning subnet {base_ip}.{start}-{end}")
        
        devices = []
        
        for i in range(start, end + 1):
            target_ip = f"{base_ip}.{i}"
            
            # Try AppleMIDI on both control and data ports
            for port in [5004, 5005]:
                device = self.send_applemidi_invitation(target_ip, port, session_name=f"Scan{i}")
                if device:
                    devices.append(device)
                    break  # Found device, move to next IP
            
            # Small delay to avoid flooding
            time.sleep(0.05)
        
        return devices
    
    def discover_device(self, target_ip: str) -> Optional[MioDevice]:
        """
        Try all discovery methods for a specific IP
        
        Args:
            target_ip: IP address to query
            
        Returns:
            MioDevice if found, None otherwise
        """
        print(f"\n{'='*70}")
        print(f"UDP Device Discovery: {target_ip}")
        print(f"{'='*70}\n")
        
        # Method 1: AppleMIDI control port
        device = self.send_applemidi_invitation(target_ip, 5004, "Query1")
        if device:
            return device
        
        # Method 2: AppleMIDI data port
        device = self.send_applemidi_invitation(target_ip, 5005, "Query2")
        if device:
            return device
        
        # Method 3: Alternative ports
        for port in [21928, 21929, 5006, 5007]:
            device = self.send_applemidi_invitation(target_ip, port, f"QueryPort{port}")
            if device:
                return device
        
        return None
    
    def discover_all(self, target_ip: Optional[str] = None) -> List[MioDevice]:
        """
        Run all discovery methods
        
        Args:
            target_ip: Optional specific IP to target
            
        Returns:
            List of all discovered devices
        """
        devices = []
        
        if target_ip:
            # Targeted discovery
            device = self.discover_device(target_ip)
            if device:
                devices.append(device)
        else:
            # Broadcast discovery
            print("\n" + "="*70)
            print("UDP Broadcast Discovery")
            print("="*70 + "\n")
            
            broadcast_devices = self.send_broadcast_discovery()
            devices.extend(broadcast_devices)
            
            # mDNS discovery
            mdns_devices = self.send_mdns_query()
            devices.extend(mdns_devices)
        
        return devices


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="UDP-based mio XL device discovery")
    parser.add_argument("ip", nargs="?", help="Target IP address")
    parser.add_argument("--scan", metavar="SUBNET", help="Scan subnet (e.g., 192.168.1)")
    parser.add_argument("--broadcast", action="store_true", help="Use broadcast discovery")
    parser.add_argument("--timeout", type=float, default=2.0, help="Timeout in seconds (default: 2.0)")
    
    args = parser.parse_args()
    
    discovery = UDPDeviceDiscovery(timeout=args.timeout)
    
    print("\n🎹 mio XL UDP Device Discovery Tool")
    print("=" * 70)
    
    devices = []
    
    if args.scan:
        # Subnet scan
        devices = discovery.scan_subnet(args.scan)
    
    elif args.broadcast:
        # Broadcast discovery
        devices = discovery.discover_all(target_ip=None)
    
    elif args.ip:
        # Targeted discovery
        device = discovery.discover_device(args.ip)
        if device:
            devices.append(device)
    
    else:
        # Default: try broadcast then specific IP if provided
        print("\nNo target specified. Use --help for options.\n")
        print("Examples:")
        print("  python3 udp_device_discovery.py 192.168.1.199")
        print("  python3 udp_device_discovery.py --scan 192.168.1")
        print("  python3 udp_device_discovery.py --broadcast")
        sys.exit(1)
    
    # Display results
    print("\n" + "="*70)
    print("DISCOVERY RESULTS")
    print("="*70 + "\n")
    
    if devices:
        print(f"✅ Found {len(devices)} device(s):\n")
        
        for i, device in enumerate(devices, 1):
            print(f"{i}. {device.name}")
            print(f"   IP: {device.ip}:{device.port}")
            print(f"   Protocol: {device.protocol}")
            if device.ssrc:
                print(f"   SSRC: 0x{device.ssrc:08x}")
            if device.token:
                print(f"   Token: 0x{device.token:08x}")
            print()
    else:
        print("❌ No devices found\n")
        print("Troubleshooting:")
        print("  • Verify device is powered on and connected to network")
        print("  • Check device has network MIDI enabled (may require USB config)")
        print("  • Try scanning your subnet: --scan 192.168.1")
        print("  • Device may need to be configured via USB first")
        print()
    
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
