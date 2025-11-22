# Connection Guide

## Overview

This guide describes how to connect to and communicate with the mio XL MIDI interface for protocol analysis and development.

## Prerequisites

### Hardware Requirements
- mio XL MIDI interface
- USB cable (Type-B to Type-A)
- Computer with available USB port
- (Optional) MIDI devices for testing

### Software Requirements
- Python 3.7 or higher
- Required Python packages:
  - pyserial
  - pyusb (for low-level USB access)
  - mido or python-rtmidi (for MIDI communication)

## Physical Connection

### Step 1: Connect Hardware
1. Connect the mio XL to your computer via USB
2. Wait for the device to enumerate
3. Check that the device is recognized by the system

### Step 2: Verify Connection

#### On Linux:
```bash
# List USB devices
lsusb | grep -i midi

# Check for MIDI ports
ls /dev/midi*
ls /dev/snd/midi*

# View device details
cat /proc/asound/cards
```

#### On macOS:
```bash
# List USB devices
system_profiler SPUSBDataType | grep -A 10 -i midi

# Check MIDI devices
ls /dev/cu.usb*
```

#### On Windows:
```powershell
# List devices in Device Manager
Get-PnpDevice | Where-Object {$_.FriendlyName -like "*MIDI*"}

# Or check manually in Device Manager
# Look under "Sound, video and game controllers"
```

## Software Connection

### Using Python with python-rtmidi

```python
import rtmidi

# List available MIDI input ports
midiin = rtmidi.MidiIn()
print("Input ports:")
for i, port in enumerate(midiin.get_ports()):
    print(f"  {i}: {port}")

# List available MIDI output ports
midiout = rtmidi.MidiOut()
print("\nOutput ports:")
for i, port in enumerate(midiout.get_ports()):
    print(f"  {i}: {port}")

# Connect to a port
port_index = 0  # Adjust based on your system
midiin.open_port(port_index)
print(f"\nConnected to input port: {midiin.get_ports()[port_index]}")
```

### Using Python with mido

```python
import mido

# List available MIDI ports
print("Input ports:")
for port in mido.get_input_names():
    print(f"  {port}")

print("\nOutput ports:")
for port in mido.get_output_names():
    print(f"  {port}")

# Open a port
port_name = mido.get_input_names()[0]  # First available port
with mido.open_input(port_name) as inport:
    print(f"Connected to: {port_name}")
    
    # Read MIDI messages
    for message in inport:
        print(message)
```

### Using the Project's Analyzers

```python
from analyzers import SerialAnalyzer

# For MIDI analysis via serial port
analyzer = SerialAnalyzer(
    port='/dev/ttyUSB0',  # Adjust for your system
    baudrate=31250  # MIDI baud rate
)

if analyzer.connect():
    print("Connected to MIDI device")
    
    # Capture MIDI traffic
    data = analyzer.capture(duration=10)
    print(f"Captured {len(data)} bytes")
    
    analyzer.disconnect()
```

## USB-Level Access

### Using PyUSB for Low-Level Access

```python
import usb.core
import usb.util

# Find the mio XL device
# Replace vendor_id and product_id with actual values
vendor_id = 0x2321  # Example - check with lsusb
product_id = 0x????  # Example - check with lsusb

dev = usb.core.find(idVendor=vendor_id, idProduct=product_id)

if dev is None:
    print("Device not found")
else:
    print(f"Found device: {dev}")
    
    # Get device descriptor
    print(f"Manufacturer: {usb.util.get_string(dev, dev.iManufacturer)}")
    print(f"Product: {usb.util.get_string(dev, dev.iProduct)}")
    print(f"Serial: {usb.util.get_string(dev, dev.iSerialNumber)}")
    
    # Print configuration
    cfg = dev.get_active_configuration()
    print(f"Configuration: {cfg}")
```

## Protocol Analysis Setup

### Capturing USB Traffic

#### On Linux (using usbmon):
```bash
# Load usbmon module
sudo modprobe usbmon

# Find bus number
lsusb | grep -i midi

# Capture traffic (replace X with bus number)
sudo cat /sys/kernel/debug/usb/usbmon/Xu

# Or use Wireshark
sudo wireshark
# Select usbmonX interface
```

#### On Windows (using USBPcap):
1. Install USBPcap (comes with Wireshark)
2. Start Wireshark
3. Select USB bus where mio XL is connected
4. Apply filter: `usb.idVendor == 0x2321` (adjust vendor ID)

### Capturing MIDI Traffic

```python
import mido

# Monitor all incoming MIDI messages
port_name = mido.get_input_names()[0]

with mido.open_input(port_name) as inport:
    print(f"Monitoring {port_name}")
    print("Press Ctrl+C to stop\n")
    
    try:
        for msg in inport:
            print(f"{msg.time:.3f} - {msg}")
    except KeyboardInterrupt:
        print("\nStopped monitoring")
```

## Troubleshooting

### Permission Issues (Linux)

```bash
# Add user to dialout group for serial port access
sudo usermod -a -G dialout $USER

# For USB raw access, create udev rule
echo 'SUBSYSTEM=="usb", ATTRS{idVendor}=="2321", MODE="0666"' | \
  sudo tee /etc/udev/rules.d/50-mio-xl.rules

# Reload udev rules
sudo udevadm control --reload-rules
sudo udevadm trigger
```

### Device Not Recognized

1. Check USB cable connection
2. Try a different USB port
3. Verify device powers on (check LEDs)
4. Update USB drivers (Windows)
5. Check system logs:
   - Linux: `dmesg | tail`
   - macOS: Console.app
   - Windows: Device Manager

### MIDI Data Not Flowing

1. Verify port is not in use by another application
2. Check MIDI connections are correct
3. Ensure device is not muted in system settings
4. Test with known-working MIDI software
5. Verify MIDI cables are functional (if using hardware MIDI)

## Testing the Connection

### Basic Connection Test

```python
import mido
import time

# Open output port
port_name = mido.get_output_names()[0]
with mido.open_output(port_name) as outport:
    print(f"Sending test message to {port_name}")
    
    # Send a test note
    note_on = mido.Message('note_on', note=60, velocity=64)
    outport.send(note_on)
    time.sleep(0.5)
    
    note_off = mido.Message('note_off', note=60)
    outport.send(note_off)
    
    print("Test complete")
```

### Loopback Test

Connect a MIDI OUT port to a MIDI IN port on the mio XL:

```python
import mido

input_port = mido.open_input(mido.get_input_names()[0])
output_port = mido.open_output(mido.get_output_names()[0])

print("Sending test message...")
output_port.send(mido.Message('note_on', note=60, velocity=64))

print("Waiting for message...")
msg = input_port.receive()
print(f"Received: {msg}")

input_port.close()
output_port.close()
```

## Next Steps

After establishing a connection:

1. **Capture baseline traffic:** Record normal device operation
2. **Analyze message structure:** Identify patterns and commands
3. **Test specific features:** Exercise different device capabilities
4. **Document findings:** Record protocol details and behaviors

## References

- Python rtmidi documentation: https://spotlightkid.github.io/python-rtmidi/
- Mido documentation: https://mido.readthedocs.io/
- PyUSB documentation: https://github.com/pyusb/pyusb
- MIDI specification: https://www.midi.org/specifications
