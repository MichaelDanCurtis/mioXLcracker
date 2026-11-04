#!/usr/bin/env python3
"""
List all MIDI devices and query mioXL presets via USB if available
"""

import mido
import sys


def list_midi_devices():
    """List all available MIDI devices"""
    print("\n" + "="*70)
    print("Available MIDI Devices")
    print("="*70 + "\n")
    
    inputs = mido.get_input_names()
    outputs = mido.get_output_names()
    
    print(f"📥 Input Ports ({len(inputs)}):")
    if inputs:
        for i, name in enumerate(inputs, 1):
            marker = "🎹" if "mio" in name.lower() else "  "
            print(f"  {marker} {i}. {name}")
    else:
        print("   (none)")
    
    print(f"\n📤 Output Ports ({len(outputs)}):")
    if outputs:
        for i, name in enumerate(outputs, 1):
            marker = "🎹" if "mio" in name.lower() else "  "
            print(f"  {marker} {i}. {name}")
    else:
        print("   (none)")
    
    print()
    
    # Find mio devices
    mio_devices = [name for name in inputs if "mio" in name.lower()]
    
    return mio_devices


if __name__ == "__main__":
    print("\n🎹 USB MIDI Device Detector")
    
    mio_devices = list_midi_devices()
    
    if mio_devices:
        print("="*70)
        print(f"✅ Found {len(mio_devices)} mioXL device(s) via USB")
        print("="*70)
        print("\nTo query presets via USB, run:")
        print(f"  python3 mio_xl_tester.py")
        print("\nOr use the mioctl-based tool:")
        print(f"  python3 -c 'from mio_usb_query import *; query_device()'")
    else:
        print("="*70)
        print("❌ No mioXL devices found via USB")
        print("="*70)
        print("\nTo query presets, you need to:")
        print("  1. Connect mioXL device via USB cable")
        print("  2. The device should appear as USB MIDI device")
        print("  3. Run this script again to detect it")
        print("\nNote: Network (UDP) connection only supports MIDI data,")
        print("      not device configuration queries.")
    
    print("\n")
