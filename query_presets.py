#!/usr/bin/env python3
"""
Query mioXL presets via UDP
"""

import sys
import time
from mioxl_udp_controller import MioXLController


def query_presets(ip: str, port: int = 5006):
    """Query and display all presets from device"""
    
    print("\n🎹 mioXL Preset Query")
    print("="*70 + "\n")
    
    controller = MioXLController(ip, port)
    
    if not controller.connect("PresetQuery"):
        print("❌ Failed to connect to device")
        return
    
    print(f"\n📋 Device: {controller.device_name}")
    print(f"   IP: {ip}:{port}")
    print(f"   SSRC: 0x{controller.ssrc:08x}\n")
    
    # Query presets
    result = controller.query_presets()
    
    if result:
        presets = result.get("presets", [])
        if presets:
            print(f"\n✅ Found {len(presets)} preset(s):\n")
            for i, preset in enumerate(presets, 1):
                print(f"  {i}. {preset}")
        else:
            print("\n⚠ No presets found in response")
    
    print("\n" + "="*70)
    print("ℹ Note: Preset information is typically only available via USB")
    print("  The device accepts network MIDI for performance data only.")
    print("  For full configuration access, use USB connection.")
    print("="*70 + "\n")
    
    # Try to get any configuration info by listening
    print("🎧 Listening for any device messages...")
    print("   (waiting 5 seconds...)\n")
    
    time.sleep(5)
    
    controller.disconnect()


if __name__ == "__main__":
    ip = sys.argv[1] if len(sys.argv) > 1 else "192.168.1.199"
    query_presets(ip)
