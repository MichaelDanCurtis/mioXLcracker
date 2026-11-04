#!/usr/bin/env python3
"""
Query all mioXL network MIDI ports/presets
Connects to all discovered AppleMIDI sessions
"""

import sys
from udp_device_discovery import UDPDeviceDiscovery


def discover_all_sessions(ip: str):
    """Discover all AppleMIDI sessions on the device"""
    print("\n" + "="*70)
    print(f"🎹 mioXL Multi-Session Discovery: {ip}")
    print("="*70 + "\n")
    
    ports_to_check = range(5004, 5020)  # Check ports 5004-5019
    
    discovery = UDPDeviceDiscovery(timeout=1.0)
    sessions = []
    
    print("📡 Scanning for AppleMIDI sessions...\n")
    
    for port in ports_to_check:
        device = discovery.send_applemidi_invitation(ip, port, session_name=f"Query{port}")
        if device:
            sessions.append(device)
            print()
    
    if not sessions:
        print("❌ No sessions found")
        return
    
    print("\n" + "="*70)
    print(f"✅ Found {len(sessions)} AppleMIDI session(s)")
    print("="*70 + "\n")
    
    for i, session in enumerate(sessions, 1):
        print(f"{i}. {session.name}")
        print(f"   Port: {session.port}")
        print(f"   SSRC: 0x{session.ssrc:08x}")
        print()
    
    print("="*70)
    print("💡 Analysis:")
    print("="*70)
    print(f"\nThe device exposes {len(sessions)} different network MIDI sessions.")
    print("These could represent:")
    print("  • Different presets")
    print("  • Different MIDI ports (DIN 1-10)")
    print("  • Different routing configurations")
    print("\nThe naming pattern suggests:")
    
    for session in sessions:
        # Extract number from name like "mioXL C1F-02"
        parts = session.name.split('-')
        if len(parts) > 1:
            num = parts[-1].strip()
            print(f"  • {session.name} (Port {session.port}) → Session/Port #{num}")
    
    print("\n" + "="*70)
    print("🔬 To investigate further:")
    print("="*70)
    print("\n1. Each session might correspond to a physical/virtual MIDI port")
    print("2. Auracle X likely uses ONE session for control + config")
    print("3. Other sessions are for MIDI data routing")
    print("\n4. Try connecting to port 5006 and sending SysEx:")
    print(f"     python3 mioxl_udp_controller.py {ip} --port 5006")
    print("\n5. Or capture Auracle X traffic:")
    print(f"     sudo python3 sniff_network.py {ip} 60")
    print()


if __name__ == "__main__":
    ip = sys.argv[1] if len(sys.argv) > 1 else "192.168.1.199"
    discover_all_sessions(ip)
