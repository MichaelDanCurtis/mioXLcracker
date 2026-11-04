#!/usr/bin/env python3
"""
Network packet sniffer for mioXL communication
Captures and analyzes packets between Auracle X and the device
"""

import socket
import struct
import sys
import time
from scapy.all import sniff, IP, UDP, TCP, Raw, wrpcap
from datetime import datetime
import json


class MioXLSniffer:
    """Sniff and decode mioXL network traffic"""
    
    def __init__(self, target_ip: str):
        self.target_ip = target_ip
        self.packets_captured = []
        self.raw_packets = []
    
    def packet_callback(self, packet):
        """Process captured packet"""
        self.raw_packets.append(packet)
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        
        # Check if packet involves our target IP
        if IP in packet:
            src_ip = packet[IP].src
            dst_ip = packet[IP].dst
            
            if src_ip == self.target_ip or dst_ip == self.target_ip:
                direction = "←" if src_ip == self.target_ip else "→"
                
                # Get protocol and port info
                protocol = "???"
                port = "???"
                payload = None
                
                if UDP in packet:
                    protocol = "UDP"
                    if src_ip == self.target_ip:
                        port = packet[UDP].sport
                    else:
                        port = packet[UDP].dport
                    
                    if Raw in packet:
                        payload = bytes(packet[Raw].load)
                
                elif TCP in packet:
                    protocol = "TCP"
                    if src_ip == self.target_ip:
                        port = packet[TCP].sport
                    else:
                        port = packet[TCP].dport
                    
                    if Raw in packet:
                        payload = bytes(packet[Raw].load)
                
                # Print packet info
                print(f"\n[{timestamp}] {direction} {protocol}:{port} {src_ip} ↔ {dst_ip}")
                
                if payload:
                    print(f"  Length: {len(payload)} bytes")
                    print(f"  Hex: {payload[:64].hex()}" + ("..." if len(payload) > 64 else ""))
                    
                    # Try to identify packet type
                    self.identify_packet_type(payload)
                    
                    # Store packet
                    self.packets_captured.append({
                        'timestamp': timestamp,
                        'direction': direction,
                        'protocol': protocol,
                        'port': port,
                        'src': src_ip,
                        'dst': dst_ip,
                        'payload': payload
                    })
    
    def identify_packet_type(self, payload: bytes):
        """Identify the type of packet"""
        if len(payload) < 4:
            return
        
        # AppleMIDI control packets
        if payload[0:2] == b'\xff\xff':
            cmd = payload[2:4].decode('ascii', errors='ignore')
            types = {
                'IN': 'AppleMIDI Invitation',
                'OK': 'AppleMIDI Acceptance',
                'NO': 'AppleMIDI Rejection',
                'BY': 'AppleMIDI End Session',
                'CK': 'AppleMIDI Sync',
                'RS': 'AppleMIDI Feedback'
            }
            print(f"  Type: {types.get(cmd, 'AppleMIDI Unknown')}")
        
        # SysEx message
        elif payload[0] == 0xF0:
            print(f"  Type: SysEx Message")
            if len(payload) >= 4 and payload[1:4] == b'\x00\x01\x73':
                print(f"       Manufacturer: iConnectivity")
        
        # RTP packet
        elif len(payload) >= 12:
            vpxcc = payload[0]
            v = (vpxcc >> 6) & 0x03
            if v == 2:
                print(f"  Type: RTP-MIDI Data")
        
        # HTTP-like
        elif payload[0:4] in [b'GET ', b'POST', b'PUT ', b'DELE']:
            print(f"  Type: HTTP Request")
            try:
                print(f"       {payload[:80].decode('ascii', errors='ignore')}")
            except:
                pass
        
        # JSON
        elif payload[0] in [ord('{'), ord('[')]:
            print(f"  Type: JSON Data")
            try:
                print(f"       {payload[:100].decode('utf-8', errors='ignore')}")
            except:
                pass
        
        # Check for specific strings
        if b'beer1' in payload:
            print(f"  🍺 FOUND 'beer1' IN PACKET! 🍺")
            print(f"  Hex: {payload.hex()}")
    
    def start_capture(self, duration: int = 30):
        """Start capturing packets"""
        print("\n" + "="*70)
        print(f"📡 Sniffing network traffic to/from {self.target_ip}")
        print("="*70)
        print(f"\n⏰ Capturing for {duration} seconds...")
        print("   Now open Auracle X and interact with the device!")
        print("   (Query presets, change settings, etc.)\n")
        
        # Build filter for target IP
        filter_str = f"host {self.target_ip}"
        
        try:
            # Capture packets
            sniff(
                filter=filter_str,
                prn=self.packet_callback,
                timeout=duration,
                store=False
            )
            
            print("\n\n" + "="*70)
            print(f"✅ Capture complete! Captured {len(self.packets_captured)} packets")
            print("="*70 + "\n")
            
            # Save PCAP
            pcap_filename = f"capture_{int(time.time())}.pcap"
            print(f"💾 Saving raw packets to {pcap_filename}...")
            wrpcap(pcap_filename, self.raw_packets)
            
            self.analyze_patterns()
            
        except PermissionError:
            print("\n❌ Permission denied. Try running with sudo:")
            print(f"   sudo python3 {sys.argv[0]} {self.target_ip}")
        except Exception as e:
            print(f"\n❌ Capture error: {e}")
    
    def analyze_patterns(self):
        """Analyze captured packets for patterns"""
        if not self.packets_captured:
            print("No packets captured.")
            return
        
        print("📊 Analysis:")
        
        # Count by protocol/port
        ports = {}
        for pkt in self.packets_captured:
            key = f"{pkt['protocol']}:{pkt['port']}"
            ports[key] = ports.get(key, 0) + 1
        
        print(f"\n  Packets by port:")
        for port, count in sorted(ports.items(), key=lambda x: x[1], reverse=True):
            print(f"    {port}: {count} packets")
        
        # Look for SysEx patterns
        sysex_packets = [p for p in self.packets_captured if p['payload'][0] == 0xF0]
        if sysex_packets:
            print(f"\n  Found {len(sysex_packets)} SysEx packets!")
            print(f"  First SysEx: {sysex_packets[0]['payload'][:32].hex()}")
        
        # Look for non-standard ports
        unusual_ports = [p for p in self.packets_captured if p['port'] not in [5004, 5005, 5006, 5007]]
        if unusual_ports:
            print(f"\n  Found {len(unusual_ports)} packets on non-standard ports:")
            unique_ports = set(p['port'] for p in unusual_ports)
            for port in sorted(unique_ports):
                print(f"    Port {port}")


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("\nUsage: sudo python3 sniff_network.py <device_ip> [duration]")
        print("\nExample:")
        print("  sudo python3 sniff_network.py 192.168.1.199 60")
        print("\nNote: Requires root/sudo for packet capture")
        sys.exit(1)
    
    target_ip = sys.argv[1]
    duration = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    
    sniffer = MioXLSniffer(target_ip)
    sniffer.start_capture(duration)


if __name__ == "__main__":
    main()
