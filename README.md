# Hardware Protocol Analyzer

A Python toolkit for analyzing hardware communication protocols and understanding how applications connect to hardware devices.

## Overview

This project provides tools to analyze and understand various hardware communication protocols including:
- **Serial Protocols** (RS-232, RS-485, UART)
- **Modbus** (TCP, RTU, ASCII)
- **Network Protocols** (TCP/IP-based hardware communication)

## Features

- 📡 Serial port communication analysis
- 🔌 Modbus protocol support (TCP, RTU, ASCII)
- 🌐 Network packet capture and analysis
- 📊 Protocol traffic monitoring
- 🔍 Device scanning and discovery
- 📚 Comprehensive hardware documentation (see [Hardware_Documents](Hardware_Documents/))

## Installation

### Prerequisites
- Python 3.7 or higher
- pip package manager

### Setup

1. Clone or navigate to the project directory
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Project Structure

```
mioXLcracker/
├── analyzers/              # Protocol analyzer modules
│   ├── serial_analyzer.py  # Serial communication analyzer
│   ├── modbus_analyzer.py  # Modbus protocol analyzer
│   └── network_analyzer.py # Network traffic analyzer
├── Hardware_Documents/     # Hardware documentation
│   ├── README.md          # Documentation index
│   ├── mio_xl_overview.md # mio XL hardware overview
│   ├── protocol_specifications.md # Protocol details
│   └── connection_guide.md # Connection instructions
├── protocol_analyzer.py    # Main entry point with examples
├── requirements.txt        # Python dependencies
├── .gitignore             # Git ignore rules
└── README.md              # This file
```

## Usage

### Serial Protocol Analysis

```python
from analyzers import SerialAnalyzer

# Initialize analyzer
analyzer = SerialAnalyzer(
    port='/dev/ttyUSB0',  # or 'COM1' on Windows
    baudrate=9600,
    bytesize=8,
    parity='N',
    stopbits=1
)

# Connect and capture traffic
if analyzer.connect():
    frames = analyzer.capture(duration=10)  # Capture for 10 seconds
    print(f"Captured {len(frames)} frames")
    analyzer.disconnect()
```

### Modbus TCP Analysis

```python
import asyncio
from analyzers import ModbusAnalyzer

async def analyze_modbus():
    # Initialize Modbus TCP analyzer
    analyzer = ModbusAnalyzer(
        mode='tcp',
        host='192.168.1.100',
        port=502
    )
    
    # Connect to device
    if await analyzer.connect():
        # Read holding registers
        registers = await analyzer.read_holding_registers(0, 10, device_id=1)
        print(f"Registers: {registers}")
        
        # Scan for devices
        devices = await analyzer.scan_devices(1, 10)
        print(f"Found devices: {devices}")
        
        await analyzer.disconnect()

asyncio.run(analyze_modbus())
```

### Modbus RTU Analysis

```python
import asyncio
from analyzers import ModbusAnalyzer

async def analyze_modbus_rtu():
    # Initialize Modbus RTU analyzer
    analyzer = ModbusAnalyzer(
        mode='rtu',
        port='/dev/ttyUSB0',
        baudrate=9600,
        bytesize=8,
        parity='N',
        stopbits=1
    )
    
    if await analyzer.connect():
        # Read coils
        coils = await analyzer.read_coils(0, 10, device_id=1)
        print(f"Coils: {coils}")
        
        await analyzer.disconnect()

asyncio.run(analyze_modbus_rtu())
```

### Network Traffic Analysis

```python
from analyzers import NetworkAnalyzer

# Initialize network analyzer
analyzer = NetworkAnalyzer(
    interface='eth0',  # or None for default
    filter_str='tcp port 502'  # BPF filter for Modbus TCP
)

# Capture packets
packets = analyzer.capture(count=100, timeout=30)

# Analyze captured traffic
stats = analyzer.analyze_packets()
print(f"Total packets: {stats['total_packets']}")
print(f"Protocols: {stats['protocols']}")
print(f"Endpoints: {stats['endpoints']}")

# Save capture
analyzer.save_capture('capture.pcap')
```

## Dependencies

- **pymodbus** (>=3.1.0) - Modbus protocol implementation
- **pyserial** (>=3.5) - Serial port communication
- **scapy** (>=2.5.0) - Network packet manipulation and analysis
- **pyyaml** (>=6.0) - YAML configuration support

## Common Use Cases

### 1. Reverse Engineering Hardware Protocols
Capture and analyze communication between applications and hardware devices to understand the protocol structure.

### 2. Device Discovery
Scan networks or serial buses to discover connected hardware devices.

### 3. Protocol Debugging
Monitor and debug communication issues between software and hardware.

### 4. Protocol Documentation
Capture traffic to document undocumented or proprietary protocols.

## Notes

- **Serial Ports**: Ensure you have proper permissions to access serial ports (may require `sudo` on Linux or adding user to `dialout` group)
- **Network Capture**: Network packet capture may require root/administrator privileges
- **Modbus**: Ensure firewall rules allow connections on Modbus ports (default: TCP 502)

## Troubleshooting

### Serial Port Access Issues
```bash
# Linux: Add user to dialout group
sudo usermod -a -G dialout $USER
# Log out and log back in

# macOS: Check port name
ls /dev/tty.*

# Windows: Check Device Manager for COM port number
```

### Permission Denied on Network Capture
```bash
# Linux: Run with sudo or set capabilities
sudo setcap cap_net_raw+ep /usr/bin/python3.9
```

## License

This project is provided as-is for educational and analysis purposes.

## Contributing

Feel free to extend this toolkit with additional protocol analyzers or features!
