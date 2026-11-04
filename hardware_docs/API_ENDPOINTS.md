# mio XL API Endpoints & Protocol Documentation

## Overview
The iConnectivity mio XL MIDI interface communicates via a proprietary SysEx2 protocol over USB MIDI. The Auracle X application (version 2.3.2.845) acts as the configuration interface using a hybrid Electron/CEF architecture with native C++ backend for device communication.

## Communication Protocols

### Primary Protocols
1. **USB MIDI** - Direct device communication (REQUIRED for SysEx configuration)
2. **SysEx2** - Proprietary System Exclusive message protocol (iConnectivity)
3. **SysEx1** - Legacy System Exclusive protocol
4. **RTP-MIDI (AppleMIDI)** - Network MIDI over UDP/RTP (performance data only)
5. **Standard MIDI** - DIN MIDI I/O

### Network MIDI
- **Protocol:** RTP-MIDI / AppleMIDI
- **Session-based** connection management
- **Default Port:** Typically 5004-5005 (RTP-MIDI standard)
- **Note:** Network MIDI is for MIDI performance data (notes, CC, etc.), NOT device configuration
- **Configuration:** Requires USB MIDI connection for SysEx commands

### mioctl Protocol (Based on pmatilai/mioctl)

#### SysEx Message Structure
```
0xF0                           # SysEx Start
0x00 0x01 0x73                 # Manufacturer ID (iConnectivity)
0x7D                           # Message Class
[7 bytes device ID]            # Device ID (all zeros for broadcast)
[6 bytes foo ID]               # Unknown purpose
[2 bytes transaction ID]       # 7-bit encoded transaction counter
[2 bytes command length]       # 7-bit encoded
[1 byte flags]                 # Command flags (GET/SET/VARARG/RESPONSE)
[1 byte command ID]            # Command type (SYS/DEVICE/INFO/etc.)
[1 byte arg count]             # Number of arguments
[variable args]                # Arguments with length prefixes
[1 byte checksum]              # 128 - (sum(body) % 128)
0xF7                           # SysEx End
```

#### Command IDs
- `0x00` SYS - System commands
- `0x01` DEVICE - Device management
- `0x02` INFO - Device information queries
- `0x03` PRESET - Preset management
- `0x04` PHYSPORT - Physical port configuration
- `0x05` PORTINFO - Port information
- `0x06` MIDIPORT - MIDI port configuration

#### Command Flags
- `0x01` VARARG - Variable arguments
- `0x02` GET - Query command
- `0x10` SET - Set command
- `0x40` RESPONSE - Response message
- `0x03` QUERY - GET | VARARG (most common for queries)

#### Information IDs (INFO command)
- `0x01` DEVICE_NAME - Device name string
- `0x02` MANUFACTURER - Manufacturer string
- `0x04` SERIAL - Serial number
- `0x05` FW_VERSION - Firmware version (4 bytes)
- `0x06` HW_VERSION - Hardware version
- `0x14` NUM_PRESETS - Number of presets

#### 7-bit Encoding
Multi-byte values are encoded in 7-bit format (MSB = 0):
```python
def encode7(val, size=2):
    bd = bytearray()
    while val > 0:
        c = val & 0x7f
        val >>= 7
        bd.insert(0, c)
    while len(bd) < size:
        bd.insert(0, 0x00)
    return bd
```

#### Checksum Calculation
```python
def chksum(data):
    cs = 128 - (sum(data) % 128)
    if cs == 128:
        cs = 0
    return cs
```

---

## Device Discovery & Connection

### Discovery
```
ScanDevices()
GetDevices()
IsConnected()
```

### Device Information
```
GetDevName()
GetSerialNumber()
GetProductName()
GetFirmwareVersion()
GetHardwareVersion()
GetIsBootloader()
GetFirmwareCapable()
```

### Device Configuration
```
SetDevName(name)
SetDevUserData(data)
```

---

## MIDI Port Management

### Port Enumeration
```
GetPortCount()
GetPortType(portIndex)
GetPortHasInput(portIndex)
GetPortHasOutput(portIndex)
```

### Port Naming
```
GetPortNameIn(portIndex)
GetPortNameOut(portIndex)
SetPortName(portIndex, name)
SetPortNameIn(portIndex, name)
SetPortNameOut(portIndex, name)
GetMIDIPortNameMax()
```

### Port Routing
```
GetPortRoute(portIndex)
SetPortRoute(portIndex, routeConfig)
GetPortConnectFlags(portIndex)
```

### Port Details
```
GetMIDIInfo()
GetMIDIPortInfo(portIndex)
GetMIDIPortDetail(portIndex)
SetMIDIPortDetail(portIndex, details)
GetDevMIDIPortInfo()
```

### MIDI Filtering
```
GetFilterChannelIn(portIndex)
GetFilterChannelOut(portIndex)
GetFilterSystemIn(portIndex)
GetFilterSystemOut(portIndex)
SetFilterChannel(portIndex, channels)
SetFilterChannelIn(portIndex, channels)
SetFilterChannelOut(portIndex, channels)
SetFilterSystem(portIndex, systemMsgs)
SetFilterSystemIn(portIndex, systemMsgs)
SetFilterSystemOut(portIndex, systemMsgs)
```

### Channel Remapping
```
GetRemapChannelIn(portIndex)
GetRemapChannelOut(portIndex)
SetRemapChannelIn(portIndex, mapping)
SetRemapChannelOut(portIndex, mapping)
GetRemapChannelInSysEx1(portIndex)
GetRemapChannelOutSysEx1(portIndex)
SetRemapChannelInSysEx1(portIndex, mapping)
SetRemapChannelOutSysEx1(portIndex, mapping)
SetRemapChannelSysEx1(portIndex, mapping)
```

---

## USB Host MIDI

### USB Device Management
```
GetUSBHostMIDIDeviceDetail(portIndex)
GetUSBHostPortNumber()
GetUSBHostProductName()
GetUSBHostSerialNumber()
GetUSBHostVendorName()
GetUSBHostReserve()
```

### USB Host Port Configuration
```
GetUSBHMIDIPName()
GetUSBHMIDIPortCount()
GetUSBHMIDIPortCountIn()
GetUSBHMIDIPortCountOut()
GetUSBHMIDISerialNum()
GetUSBHMIDIVName()
```

### USB Device Jack
```
GetUSBDJackNumber()
GetUSBDPortCount()
```

### USB Reservation
```
GetUSBReservePortNumber()
GetUSBReserveProductName()
GetUSBReserveSerialNumber()
GetUSBReserveVendorName()
SetUSBReservation(config)
ClearUSBReservation()
SetUSBReserveVendorID(index, vid)
SetUSBReserveProductID(index, pid)
```

### USB HID
```
SetUSBHID(portIndex, enabled)
```

---

## Audio Configuration

### Audio Modes
```
GetAudio2Mode()
GetAudio4Mode()
```

### Sample Rate & Clock
```
GetAudioSampleRate()
SetAudioSampleRate(rate)
GetAudioClockSource()
SetAudioClockSource(source)
GetAudioBitDepth()
SetAudioBitDepth(bits)
```

### Audio Channels
```
GetAudioChannelData(channel)
GetAudioChannelsData()
```

### Audio Control
```
GetAudioControlDetailValue(control)
SetAudioControlDetailValue(control, value)
GetAudioAutomationControlEntry(index)
SetAudioAutomationControlEntry(index, entry)
```

### Audio Trigger
```
GetAudioTriggerLevel()
SetAudioTriggerLevel(level)
GetAudioTriggerChannel()
SetAudioTriggerChannel(channel)
GetAudioTimeout()
SetAudioTimeout(timeout)
```

### Audio Metering
```
GetAudioPortSourceMeters(portIndex)
GetAudioPortDestinationMeters(portIndex)
GetAudioPortMeterValue(portIndex)
```

### Volume & Gain
```
GetVolumeLevel(port, channel, type)
SetVolumeLevel(port, channel, type, value)
GetMuteStatus(port, channel, type)
SetMuteStatus(port, channel, type, muted)
GetStereoStatus(channel)
SetStereoStatus(channel, stereo)
```

### Input Configuration
```
GetPhantomPowerStatus(channel)
SetPhantomPowerStatus(channel, enabled)
GetHighImpedanceStatus(channel)
SetHighImpedanceStatus(channel, enabled)
GetHeadphoneSetupStatus()
```

---

## Audio Mixer

### Mixer Input Controls
```
GetMixerInputLevel(mixer, input, channel)
SetMixerInputLevel(mixer, input, channel, level)
GetMixerInputMute(mixer, input, channel)
SetMixerInputMute(mixer, input, channel, muted)
GetMixerInputSolo(mixer, input, channel)
SetMixerInputSolo(mixer, input, channel, solo)
GetMixerInputStereo(mixer, input, channel)
SetMixerInputStereo(mixer, input, channel, stereo)
GetMixerInputPan(mixer, input, channel)
SetMixerInputPan(mixer, input, channel, pan)
GetMixerInputControlValue(mixer, input)
SetMixerInputControlValue(mixer, input, value)
```

### Mixer Output Controls
```
GetMixerOutputLevel(mixer)
SetMixerOutputLevel(mixer, level)
GetMixerOutputMute(mixer)
SetMixerOutputMute(mixer, muted)
GetMixerOutputMuteStatus(mixer)
SetMixerOutputMuteStatus(mixer, muted)
GetMixerOutputControlValue(mixer)
SetMixerOutputControlValue(mixer, value)
```

### Mixer Metering
```
GetMixerMeters(mixer)
GetMixerMeterValue(mixer)
```

---

## Network/Ethernet Configuration

### IP Configuration
```
GetEthCurrentIp()
SetEthCurrentIp(ip)
GetEthDynamicAddressing()
SetEthDynamicAddressing(enabled)
SetEthStaticIP(ip)
```

### IP Addressing (Receiver/Transmitter)
```
GetEthIPAddressR()
GetEthIPAddressX()
SetEthIPAddressR(ip)
```

### Port Configuration
```
GetEthPortNumber()
GetEthPortNumberR()
GetEthPortNumberX()
SetEthPortNumberR(port)
```

### RTP-MIDI Sessions
```
GetEthSesnName()
GetEthSesnNameN(index)
GetEthSesnNameR()
GetEthSesnNameX()
SetEthSesnName(name)
SetEthSesnNameR(name)
GetEthSesnFlags()
SetEthSesnFlags(flags)
GetRTPMIDIConnectionDetail(index)
GetRTPMIDIConnectionParm(index)
SetRTPMIDIConnectionParm(index, params)
```

### Saved Sessions
```
GetSavedSession()
SetSavedSession(session)
```

---

## Presets & Scenes

### Preset Management
```
GetPresetMax()
GetPresetNumber()
GetPresetName(index)
GetPresetNameMax()
SetPresetName(index, name)
GetCurrentPresetName()
```

### Network Session Discovery (RTP-MIDI)
The mioXL exposes multiple concurrent RTP-MIDI (AppleMIDI) session endpoints which can be queried via invitation packets (signature `0xFFFF`, command `"IN"`). Each accepted session returns an `OK` packet containing:

```
0xFFFF 'OK' <protocolVersion:4> <initiatorToken:4> <ssrc:4> <sessionName\x00>
```

Discovered example (device at 192.168.1.199):

| Port | Response | Session Name    | SSRC (hex) |
|------|----------|-----------------|------------|
| 5006 | OK       | mioXL C1F-02    | 0x00000020 |
| 5008 | OK       | mioXL C1F-03    | 0x00000021 |
| 5010 | OK       | mioXL C1F-04    | 0x00000022 |
| 5012 | OK       | mioXL C1F-05    | 0x00000023 |
| 5014 | OK       | mioXL C1F-06    | 0x00000024 |
| 5016 | OK       | mioXL C1F-07    | 0x00000025 |
| 5018 | OK       | mioXL C1F-08    | 0x00000026 |

Ports 5004, 5005, 5007, 5009, 5011, 5013, 5015, 5017 responded with `NO` (rejection).

Interpretation: These accepted ports correspond to distinct network MIDI streams (virtual MIDI ports) rather than stored "presets". Device configuration (preset enumeration / naming) is not returned via the simple SysEx-over-RTP embedding attempted so far.

### Attempted Network Preset Queries
SysEx frames (manufacturer ID `00 01 73`, class `0x7D`) mirroring USB queries were embedded directly into RTP-MIDI payloads:

- Query number of presets (INFO / NUM_PRESETS `0x14`)
- Query current preset (PRESET / current `0x01`)
- Query preset name indexes 1..10

All produced zero or no application-layer responses over RTP-MIDI, despite an accepted AppleMIDI session. This indicates one of:

1. Preset/config SysEx is restricted to the USB transport.
2. An additional enable/authentication or capability negotiation message precedes config responses on network.
3. Auracle X encapsulates configuration differently (e.g., proprietary block / journaling flags / alternate port).

### Next Steps (Reverse Engineering Guidance)
1. Capture live Auracle X traffic while performing preset operations:
    - Start sniff: `sudo python3 sniff_network.py <device_ip> 60`
    - In Auracle X: list presets, switch presets, rename.
    - Examine captured packets for larger RTP payloads containing SysEx (`F0 ... F7`) or non-standard control frames.
2. Identify any preamble / handshake before first config reply.
3. Compare transaction IDs and flags with USB SysEx (mioctl) to spot differences.
4. If a proprietary wrapper is present, map its structure (length fields, checksums, routing indicators).

### Known SysEx Structure (Recap)
```
F0 00 01 73 7D <7 bytes devID> <6 bytes fooID>
<2 bytes txn 7-bit> <2 bytes cmdLen 7-bit> <flags> <cmdId> <nArgs> <argBlocks...> <checksum> F7
```
Where checksum = (128 - (sum(body) % 128)) & 0x7F.

### Recommendation
Until packet captures reveal the network-specific adaptation layer, use USB for reliable preset management. Network RTP-MIDI session enumeration is fully functional and can be used for MIDI performance streaming across multiple virtual ports.


### Scene Management
```
GetScene()
SetScene(sceneIndex)
GetAutoSwitchScene()
SetAutoSwitchScene(enabled)
```

---

## Control Surface

### Control Configuration
```
GetControlEnable(controlIndex)
SetControlEnable(controlIndex, enabled)
GetControlState(controlIndex)
GetControlEvent(controlIndex)
SetControlEvent(controlIndex, event)
GetControlInput(controlIndex)
SetControlInput(controlIndex, input)
GetControlInvert(controlIndex)
SetControlInvert(controlIndex, inverted)
GetControlMomentary(controlIndex)
SetControlMomentary(controlIndex, momentary)
```

---

## Trigger & Failover

### MIDI Trigger
```
GetMidiTriggerLevel()
SetMidiTriggerLevel(level)
GetMidiTriggerChannel()
SetMidiTriggerChannel(channel)
GetMidiTimeout()
SetMidiTimeout(timeout)
GetTriggerMode()
SetTriggerMode(mode)
```

### MIDI Recovery/Failover
```
GetMidiRecoveryMode()
SetMidiRecoveryMode(mode)
GetRecoveryPorts()
SetRecoveryPorts(ports)
GetRecoveryChannels()
SetRecoveryChannels(channels)
GetRecoveryFlags()
SetRecoveryFlags(flags)
```

### Failover Configuration
```
GetFailoverMode()
SetFailoverMode(mode)
GetFailoverArmed()
SetFailoverArmed(armed)
GetFailoverAlarm()
GetFailoverClearAlarm()
SetFailoverClearAlarm()
ClearFailoverAlarm()
GetFailoverMidiPanic()
SetFailoverMidiPanic(enabled)
```

### Auto-Arm
```
GetAutoArm()
SetAutoArm(enabled)
```

---

## MIDI GOB (Group of Bytes)

### GOB Configuration
```
GetMidiGob(index)
SetMidiGob(index, gob)
GetMidiGobSize(index)
SetMidiGobSize(index, size)
```

---

## Virtual Ports

### Port Creation
```
CreateVirtualPort(config)
```

---

## Firmware Management

### Firmware Operations
```
UpdateFirmware(firmwareData)
```

---

## Data Types & Parameters

### Common Parameters
- **portIndex**: Integer (0-based index of MIDI port)
- **mixer**: Integer (mixer number)
- **input/channel**: Integer (input/channel number)
- **level/value**: Double (0.0 to 1.0 or device-specific range)
- **muted/enabled**: Boolean
- **name**: String
- **ip**: String (IPv4 address format)
- **port**: Integer (network port number)

### Port Types
- DIN MIDI (5-pin)
- USB Device MIDI
- USB Host MIDI
- Network MIDI (RTP-MIDI)
- Virtual MIDI

### Sample Rates (Audio)
Common values: 44100, 48000, 88200, 96000 Hz

### Bit Depths (Audio)
Common values: 16, 24 bits

---

## Protocol Notes

### SysEx2 Message Structure
The device uses a proprietary SysEx2 protocol for configuration. Messages appear to follow this general structure:
- Uses standard MIDI SysEx format (0xF0 ... 0xF7)
- Manufacturer ID: iConnectivity
- Command/query structure with response messages
- Supports asynchronous messaging via futures/promises

### Network MIDI (RTP-MIDI)
- Session-based protocol
- Requires session name configuration
- Supports multiple simultaneous sessions
- Compatible with Apple's network MIDI implementation

### USB Communication
- Standard USB MIDI class compliance
- Additional USB Host mode for connecting MIDI devices
- USB reservation system for persistent device assignment

---

## Application Architecture

### Auracle X (v2.3.2.845)
- **Frontend**: React 17.0.2 + Material-UI 4.12.4
- **Backend**: Native C++ with Chromium Embedded Framework
- **Bundle ID**: com.iconnectivity.auracle
- **Update URL**: https://cdn.iconnectivity.com/armcast.xml
- **Minimum macOS**: 10.13

### Communication Flow
```
React UI → Electron IPC → Native C++ → USB MIDI → mio XL Device
                                    ↓
                            RTP-MIDI (Network)
```

---

## References
- Extracted from Auracle X application binary analysis
- Based on iConnectivity mio XL hardware
- SysEx2 protocol is proprietary to iConnectivity

---

**Document Version**: 1.0  
**Date**: November 22, 2025  
**Source**: Binary analysis of Auracle X v2.3.2.845
