"""
mio XL Device Tester
Tests basic communication and control features with iConnectivity mio XL
"""

import mido
import time
import sys
from typing import Optional, List, Dict


class MioXLTester:
    """Test interface for iConnectivity mio XL MIDI device"""
    
    # iConnectivity Manufacturer ID for SysEx
    MANUFACTURER_ID = [0x00, 0x01, 0x73]  # iConnectivity
    
    def __init__(self, device_name: Optional[str] = None):
        """
        Initialize connection to mio XL device.
        
        Args:
            device_name: MIDI port name, or None to auto-detect
        """
        self.port_name = device_name
        self.input_port = None
        self.output_port = None
        self.device_id = 0x00  # Default device ID
        
    def list_midi_ports(self):
        """List all available MIDI ports"""
        print("\n=== Available MIDI Input Ports ===")
        input_ports = mido.get_input_names()
        for i, port in enumerate(input_ports):
            print(f"{i}: {port}")
        
        print("\n=== Available MIDI Output Ports ===")
        output_ports = mido.get_output_names()
        for i, port in enumerate(output_ports):
            print(f"{i}: {port}")
        
        return input_ports, output_ports
    
    def connect(self, port_name: Optional[str] = None):
        """
        Connect to mio XL device.
        
        Args:
            port_name: Specific port name, or None to search for mio
        """
        if port_name:
            self.port_name = port_name
        else:
            # Try to find mio XL in available ports
            input_ports = mido.get_input_names()
            output_ports = mido.get_output_names()
            
            for port in input_ports:
                if 'mio' in port.lower() or 'iconnectivity' in port.lower():
                    self.port_name = port
                    break
            
            if not self.port_name:
                raise Exception("Could not find mio XL device. Please specify port name.")
        
        try:
            self.output_port = mido.open_output(self.port_name)
            self.input_port = mido.open_input(self.port_name)
            print(f"✓ Connected to {self.port_name}")
            return True
        except Exception as e:
            print(f"✗ Failed to connect: {e}")
            return False
    
    def disconnect(self):
        """Close MIDI ports"""
        if self.input_port:
            self.input_port.close()
        if self.output_port:
            self.output_port.close()
        print("✓ Disconnected")
    
    def send_sysex(self, data: List[int], description: str = ""):
        """
        Send SysEx message to device.
        
        Args:
            data: SysEx data (without F0/F7 markers)
            description: Description of command
        """
        if not self.output_port:
            print("✗ Not connected")
            return False
        
        message = mido.Message('sysex', data=data)
        if description:
            print(f"→ Sending: {description}")
        print(f"  Data: {' '.join(f'{b:02X}' for b in data)}")
        
        try:
            self.output_port.send(message)
            return True
        except Exception as e:
            print(f"✗ Send failed: {e}")
            return False
    
    def receive_sysex(self, timeout: float = 2.0) -> Optional[List[int]]:
        """
        Receive SysEx response from device.
        
        Args:
            timeout: Maximum time to wait for response
            
        Returns:
            SysEx data or None if timeout
        """
        if not self.input_port:
            print("✗ Not connected")
            return None
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            msg = self.input_port.receive(block=False)
            if msg and msg.type == 'sysex':
                print(f"← Received: {' '.join(f'{b:02X}' for b in msg.data)}")
                return msg.data
            time.sleep(0.01)
        
        print("✗ Timeout waiting for response")
        return None
    
    def send_and_receive(self, data: List[int], description: str = "", timeout: float = 2.0):
        """Send SysEx and wait for response"""
        if self.send_sysex(data, description):
            return self.receive_sysex(timeout)
        return None
    
    def query_device_info(self):
        """Query basic device information"""
        print("\n=== Querying Device Information ===")
        
        # Query device name (example command structure)
        # Note: Actual command bytes need to be determined from protocol analysis
        cmd = self.MANUFACTURER_ID + [0x01, self.device_id, 0x00]  # Get device name
        response = self.send_and_receive(cmd, "Get Device Name")
        
        if response:
            print("Device responded!")
            # Parse response here
        else:
            print("No response from device")
    
    def get_preset_count(self) -> Optional[int]:
        """Get maximum number of presets"""
        print("\n=== Getting Preset Count ===")
        
        # Command to get preset max
        cmd = self.MANUFACTURER_ID + [0x02, self.device_id, 0x00]  # Get preset max
        response = self.send_and_receive(cmd, "Get Preset Count")
        
        if response and len(response) > 5:
            # Parse preset count from response
            preset_count = response[5]
            print(f"✓ Device has {preset_count} presets")
            return preset_count
        
        return None
    
    def get_preset_name(self, preset_index: int) -> Optional[str]:
        """
        Get name of specific preset.
        
        Args:
            preset_index: Preset number (0-based)
        """
        print(f"\n=== Getting Preset {preset_index} Name ===")
        
        # Command to get preset name
        cmd = self.MANUFACTURER_ID + [0x03, self.device_id, preset_index]
        response = self.send_and_receive(cmd, f"Get Preset {preset_index} Name")
        
        if response and len(response) > 5:
            # Parse name from response (ASCII characters)
            name_data = response[5:]
            # Remove any null terminators
            name = ''.join(chr(b) for b in name_data if b > 0)
            print(f"✓ Preset {preset_index}: '{name}'")
            return name
        
        return None
    
    def list_all_presets(self):
        """List all available preset names"""
        print("\n=== Listing All Presets ===")
        
        # First get preset count
        preset_count = self.get_preset_count()
        
        if preset_count:
            presets = {}
            for i in range(preset_count):
                name = self.get_preset_name(i)
                if name:
                    presets[i] = name
                time.sleep(0.1)  # Small delay between queries
            
            print("\n✓ All Presets:")
            for idx, name in presets.items():
                print(f"  [{idx}] {name}")
            
            return presets
        
        return None
    
    def change_preset(self, preset_index: int):
        """
        Change to specific preset.
        
        Args:
            preset_index: Preset number to switch to
        """
        print(f"\n=== Changing to Preset {preset_index} ===")
        
        # Command to change preset
        cmd = self.MANUFACTURER_ID + [0x04, self.device_id, preset_index]
        response = self.send_and_receive(cmd, f"Change to Preset {preset_index}")
        
        if response:
            print(f"✓ Successfully changed to preset {preset_index}")
            return True
        else:
            print(f"✗ Failed to change preset")
            return False
    
    def rename_device(self, new_name: str):
        """
        Rename the device.
        
        Args:
            new_name: New device name (max 16 characters)
        """
        print(f"\n=== Renaming Device to '{new_name}' ===")
        
        # Truncate name if too long
        if len(new_name) > 16:
            new_name = new_name[:16]
            print(f"⚠ Name truncated to: '{new_name}'")
        
        # Convert name to ASCII bytes
        name_bytes = [ord(c) for c in new_name]
        
        # Command to set device name
        cmd = self.MANUFACTURER_ID + [0x05, self.device_id] + name_bytes
        response = self.send_and_receive(cmd, f"Set Device Name")
        
        if response:
            print(f"✓ Device renamed to '{new_name}'")
            return True
        else:
            print(f"✗ Failed to rename device")
            return False
    
    def reboot_device(self):
        """Reboot the device"""
        print("\n=== Rebooting Device ===")
        print("⚠ Warning: Device will restart!")
        
        confirm = input("Continue? (yes/no): ")
        if confirm.lower() != 'yes':
            print("✗ Reboot cancelled")
            return False
        
        # Command to reboot device
        cmd = self.MANUFACTURER_ID + [0x06, self.device_id, 0x01]
        
        # Send reboot command (may not get response)
        self.send_sysex(cmd, "Reboot Device")
        print("✓ Reboot command sent")
        print("⚠ Device is rebooting... Please wait 10-15 seconds before reconnecting")
        
        # Close connection since device will disconnect
        self.disconnect()
        return True


def main():
    """Main test application"""
    print("=" * 60)
    print("mio XL Device Tester")
    print("=" * 60)
    
    tester = MioXLTester()
    
    # List available MIDI ports
    input_ports, output_ports = tester.list_midi_ports()
    
    if not output_ports:
        print("\n✗ No MIDI ports found!")
        return
    
    # Prompt for port selection
    print("\n" + "=" * 60)
    port_name = input("Enter MIDI port name (or press Enter to auto-detect): ").strip()
    
    if not port_name:
        port_name = None
    
    # Connect to device
    try:
        if not tester.connect(port_name):
            return
    except Exception as e:
        print(f"\n✗ Connection failed: {e}")
        return
    
    # Interactive menu
    while True:
        print("\n" + "=" * 60)
        print("Test Menu:")
        print("  1. Query Device Info")
        print("  2. List All Presets")
        print("  3. Change Preset")
        print("  4. Rename Device")
        print("  5. Reboot Device")
        print("  6. Send Custom SysEx")
        print("  0. Disconnect and Exit")
        print("=" * 60)
        
        choice = input("\nSelect option: ").strip()
        
        if choice == '1':
            tester.query_device_info()
        
        elif choice == '2':
            tester.list_all_presets()
        
        elif choice == '3':
            preset_idx = input("Enter preset number: ").strip()
            try:
                tester.change_preset(int(preset_idx))
            except ValueError:
                print("✗ Invalid preset number")
        
        elif choice == '4':
            new_name = input("Enter new device name: ").strip()
            if new_name:
                tester.rename_device(new_name)
        
        elif choice == '5':
            tester.reboot_device()
            break  # Exit after reboot
        
        elif choice == '6':
            hex_data = input("Enter SysEx data (hex, space-separated): ").strip()
            try:
                data = [int(b, 16) for b in hex_data.split()]
                tester.send_and_receive(data, "Custom SysEx")
            except ValueError:
                print("✗ Invalid hex data")
        
        elif choice == '0':
            tester.disconnect()
            break
        
        else:
            print("✗ Invalid option")
    
    print("\n" + "=" * 60)
    print("Testing complete!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n✗ Interrupted by user")
        sys.exit(0)
