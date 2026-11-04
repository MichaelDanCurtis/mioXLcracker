# mio XL Device Tester

Interactive testing application for iConnectivity mio XL MIDI interface.

## Features

- ✅ Device discovery and connection
- ✅ List all presets
- ✅ Change presets
- ✅ Rename device
- ✅ Reboot device
- ✅ Send custom SysEx commands

## Installation

```bash
pip install -r requirements-midi.txt
```

## Usage

```bash
python mio_xl_tester.py
```

The application will:
1. List all available MIDI ports
2. Connect to mio XL (auto-detect or manual selection)
3. Provide an interactive menu for testing

## Menu Options

1. **Query Device Info** - Get basic device information
2. **List All Presets** - Display all available preset names
3. **Change Preset** - Switch to a specific preset
4. **Rename Device** - Change the device name
5. **Reboot Device** - Restart the device
6. **Send Custom SysEx** - Send raw SysEx commands for testing

## Important Notes

⚠️ **Protocol Commands**: The SysEx command bytes in this tester are placeholders. Actual command structure needs to be determined through:
- USB packet capture with Wireshark
- Analyzing communication between Auracle X and the device
- Reverse engineering the SysEx2 protocol

### Current Command Structure (Placeholder)
```
[Manufacturer ID: 0x00, 0x01, 0x73] [Command] [Device ID] [Data...]
```

### To Capture Real Commands:
1. Install Wireshark with USB capture
2. Filter for USB MIDI traffic
3. Perform actions in Auracle X
4. Analyze SysEx messages
5. Update command bytes in this script

## Protocol Discovery

To discover the actual SysEx commands:

```bash
# Capture USB traffic
# macOS:
sudo tcpdump -i any -w mio_capture.pcap

# Then analyze with Wireshark filtering for:
# - USB MIDI (if using USB sniffer)
# - MIDI SysEx messages (F0 ... F7)
```

## Example Output

```
=== Available MIDI Output Ports ===
0: mio XL Port 1
1: mio XL Port 2

→ Sending: Get Preset Count
  Data: 00 01 73 02 00 00
← Received: 00 01 73 02 00 08
✓ Device has 8 presets

✓ All Presets:
  [0] Factory Default
  [1] Studio Setup
  [2] Live Performance
  ...
```

## Development

To extend functionality:

1. Add new test functions to `MioXLTester` class
2. Update menu in `main()` function
3. Document command structure in `hardware_docs/`

## See Also

- `hardware_docs/API_ENDPOINTS.md` - Complete API documentation
- `protocol_analyzer.py` - General protocol analysis tools
