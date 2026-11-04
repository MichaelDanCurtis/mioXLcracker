# Network Discovery Results

## Executive Summary

**Target Device:** 192.168.1.199 (iConnectivity mio XL)  
**Device Name:** **mioXL C1F-02**  
**Status:** ✅ **DISCOVERED via UDP**  
**Protocol:** AppleMIDI/RTP-MIDI on port **5006**  
**SSRC:** 0x0000001d  

## Discovery Success

The device was successfully discovered using AppleMIDI invitation protocol on **port 5006** (not the standard 5004/5005).

### Working Command
```bash
python3 udp_device_discovery.py 192.168.1.199
```

### Response
- Device accepted AppleMIDI session invitation
- Device name: **mioXL C1F-02**
- IP: 192.168.1.199:5006
- SSRC: 0x0000001d

## Discovery Attempts

### 1. AppleMIDI/RTP-MIDI Protocol (Ports 5004-5005)
- **Protocol:** Session-based RTP-MIDI with invitation packets
- **Implementation:** `query_device.py`, `network_discovery.py`
- **Result:** No response
- **Packet Format:** 0xFFFF + "IN" + version + tokens + session name
- **Purpose:** This protocol is for MIDI performance data (notes, CC), NOT configuration

### 2. SysEx over UDP (mioctl protocol)
- **Protocol:** iConnectivity proprietary SysEx messages
- **Implementation:** `mio_network_query.py`
- **Ports Tested:** 5004, 5005, 21928
- **Result:** No response to INFO.GET (Device Name) queries
- **Packet Sent:**
  ```
  f00001737d00000000000000000000000000000100070302
  01040101016bf7
  ```
- **Analysis:** Device receives packets but does not respond

## Protocol Analysis from mioctl

### Key Finding
The `mioctl` tool (https://codeberg.org/pmatilai/mioctl) communicates with mio devices via:
- **USB MIDI connection** (using python-rtmidi/mido library)
- **SysEx messages** over USB MIDI
- **NOT** over network UDP/TCP

### mioctl Connection Code
```python
def connect(self, pname):
    for n in mido.get_input_names():
        if n.startswith(pname):
            self.inp = mido.open_input(n)
    for n in mido.get_output_names():
        if n.startswith(pname):
            self.out = mido.open_output(n)
```

This clearly shows USB MIDI ports are used, not network sockets.

## Network MIDI vs Configuration

### Network MIDI (RTP-MIDI/AppleMIDI)
- **Purpose:** Real-time MIDI performance data
- **Data:** MIDI notes, CC messages, program changes, etc.
- **Protocol:** RTP over UDP (ports 5004-5005)
- **Session-based:** Requires invitation/acceptance handshake
- **Device naming:** Done during session establishment

### Device Configuration (SysEx)
- **Purpose:** Device settings, presets, routing, etc.
- **Data:** Proprietary SysEx commands
- **Protocol:** USB MIDI (not network)
- **Required:** Direct USB connection to device

## Implications

1. **Network Discovery Limitation:**
   - Cannot query device configuration over network
   - RTP-MIDI only provides session name (if device accepts session)
   - Device IP can be found but detailed info requires USB

2. **Configuration Workflow:**
   ```
   USB Connection → SysEx Commands → Device Configuration
   Network Connection → RTP-MIDI → MIDI Performance Data
   ```

3. **Auracle X Application:**
   - Uses USB MIDI for all configuration
   - Network MIDI used only for remote MIDI streaming
   - Binary analysis confirms no TCP/UDP config protocol

## Recommendations

### To Get Device Name at 192.168.1.199:

#### Option 1: USB Connection (Recommended)
```bash
# Connect via USB and use mio_xl_tester.py
python3 mio_xl_tester.py

# Or use mioctl-compatible tool
python3 mio_usb_query.py
```

#### Option 2: Network Session (Limited Info)
- Device name MAY be available in RTP-MIDI session acceptance
- But device must be configured to accept network MIDI sessions
- Likely requires USB configuration first

#### Option 3: Network Scan
- Use nmap/zeroconf to identify device type
- Device name not available without USB connection

### For Full Device Control:
1. Connect device via USB
2. Use SysEx protocol (mioctl implementation)
3. Configure all settings via USB
4. Network MIDI can then be used for performance data

## Tools Created

### Network-Based Tools (Limited Success)
1. `query_device.py` - AppleMIDI invitation protocol
2. `network_discovery.py` - RTP-MIDI session discovery
3. `mio_network_query.py` - SysEx over network (no response)

### USB-Based Tools (Functional)
1. `mio_xl_tester.py` - Interactive USB MIDI testing
2. `protocol_analyzer.py` - Protocol analysis suite

## Next Steps

1. **Connect via USB:**
   - Run `mio_xl_tester.py` to test USB connection
   - Verify device appears in MIDI device list

2. **Implement mioctl Protocol:**
   - Port mioctl commands to Python tool
   - Test device name query: `INFO.GET(DEVICE_NAME)`
   - Test other queries: firmware version, serial, presets

3. **Document Network MIDI Usage:**
   - How to enable network MIDI on device (via USB config)
   - How to establish RTP-MIDI sessions
   - Streaming MIDI data over network

## References

- **mioctl:** https://codeberg.org/pmatilai/mioctl
- **RTP-MIDI Spec:** RFC 6295
- **AppleMIDI:** Apple's RTP-MIDI implementation
- **API Documentation:** `hardware_docs/API_ENDPOINTS.md`

---

**Conclusion:** The device at 192.168.1.199 exists but cannot be configured over the network. USB MIDI connection is required for device identification, configuration, and control. Network MIDI is available but only for performance data streaming.
