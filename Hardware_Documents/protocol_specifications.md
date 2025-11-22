# Protocol Specifications

## Overview

This document describes the communication protocols used by the mio XL MIDI interface.

## USB MIDI Protocol

### USB Device Class
- **Class:** Audio (0x01)
- **Subclass:** MIDI Streaming (0x03)
- **Protocol:** USB MIDI specification

### USB Descriptors
The mio XL enumerates as a USB Audio/MIDI device with multiple MIDI streaming endpoints.

#### Key Descriptor Information
```
Device Class: Audio
Device Subclass: MIDI Streaming
bcdUSB: 2.0
idVendor: [Manufacturer-specific]
idProduct: [Product-specific]
Number of Configurations: 1
```

### USB MIDI Endpoints
- **Bulk OUT endpoint:** Host to device MIDI data
- **Bulk IN endpoint:** Device to host MIDI data
- Multiple virtual cables (one per MIDI port)

### USB MIDI Packet Format
USB MIDI uses 4-byte packets:
```
Byte 0: Cable Number (4 bits) | Code Index Number (4 bits)
Byte 1: MIDI Status Byte
Byte 2: MIDI Data Byte 1
Byte 3: MIDI Data Byte 2
```

## MIDI Protocol

### Standard MIDI Messages

#### Channel Voice Messages
| Message | Status Byte | Data Bytes |
|---------|-------------|------------|
| Note Off | 0x80-0x8F | Note, Velocity |
| Note On | 0x90-0x9F | Note, Velocity |
| Polyphonic Aftertouch | 0xA0-0xAF | Note, Pressure |
| Control Change | 0xB0-0xBF | Controller, Value |
| Program Change | 0xC0-0xCF | Program |
| Channel Aftertouch | 0xD0-0xDF | Pressure |
| Pitch Bend | 0xE0-0xEF | LSB, MSB |

#### System Common Messages
| Message | Status Byte | Data |
|---------|-------------|------|
| System Exclusive | 0xF0 | Variable length, terminated by 0xF7 |
| Time Code Quarter Frame | 0xF1 | 1 data byte |
| Song Position Pointer | 0xF2 | 2 data bytes |
| Song Select | 0xF3 | 1 data byte |
| Tune Request | 0xF6 | None |

#### System Real-Time Messages
| Message | Status Byte |
|---------|-------------|
| Timing Clock | 0xF8 |
| Start | 0xFA |
| Continue | 0xFB |
| Stop | 0xFC |
| Active Sensing | 0xFE |
| System Reset | 0xFF |

### MIDI Timing
- **Baud Rate:** 31.25 kbaud
- **Bits per byte:** 10 (1 start, 8 data, 1 stop)
- **Byte transmission time:** ~320 microseconds

## Device-Specific Features

### Port Routing
The mio XL supports flexible MIDI routing between its ports. The routing configuration may be stored in device memory or configured via proprietary messages.

### Configuration Messages
Device-specific configuration may use System Exclusive (SysEx) messages:
```
0xF0 [Manufacturer ID] [Device ID] [Command] [Parameters...] 0xF7
```

### Status Queries
The device may respond to identity request messages:
```
0xF0 0x7E [Device ID] 0x06 0x01 0xF7
```

Response format:
```
0xF0 0x7E [Device ID] 0x06 0x02 [Manufacturer ID] [Device Family] [Device Model] [Software Version] 0xF7
```

## Communication Flow

### Initialization Sequence
1. USB device enumeration
2. Host reads USB descriptors
3. Host configures device endpoints
4. MIDI ports become available to applications
5. Optional: Device configuration via SysEx

### Data Flow
1. **Host to Device (OUT):**
   - Application sends MIDI data
   - OS formats as USB MIDI packets
   - Data transmitted via USB bulk OUT endpoint
   - Device routes to appropriate MIDI OUT port
   - MIDI hardware receives standard MIDI messages

2. **Device to Host (IN):**
   - MIDI hardware sends to MIDI IN port
   - Device converts to USB MIDI packets
   - Data transmitted via USB bulk IN endpoint
   - OS delivers to MIDI application
   - Application processes MIDI messages

## Protocol Analysis Techniques

### USB Traffic Capture
- Use Wireshark with USBPcap (Windows) or usbmon (Linux)
- Filter for USB Audio/MIDI traffic
- Analyze USB MIDI packet structure

### MIDI Traffic Capture
- Use MIDI monitoring software (MIDI-OX, MIDI Monitor)
- Capture raw MIDI byte stream
- Analyze message timing and content

### System Exclusive Analysis
- Capture SysEx messages during device configuration
- Analyze command structure
- Document device-specific extensions

## References

- USB MIDI Class Specification v1.0
- MIDI 1.0 Detailed Specification
- iConnectivity mio XL documentation (if available)

## Notes

- Some features may be vendor-specific and require reverse engineering
- Always respect copyright and intellectual property when analyzing protocols
- Document findings for educational and interoperability purposes
