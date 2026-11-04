#!/usr/bin/env python3
"""
mioXL UDP Controller - Communicate with mioXL C1F-02 via network
Full UDP-based control and monitoring tool
"""

import socket
import struct
import sys
import time
import threading
from enum import IntEnum
from typing import Optional, Callable


class AppleMIDICommand(IntEnum):
    """AppleMIDI protocol commands"""
    INVITATION = 0x494E  # 'IN'
    INVITATION_ACCEPTED = 0x4F4B  # 'OK'
    INVITATION_REJECTED = 0x4E4F  # 'NO'
    END_SESSION = 0x4259  # 'BY'
    SYNCHRONIZATION = 0x434B  # 'CK'
    RECEIVER_FEEDBACK = 0x5253  # 'RS'


class MioXLController:
    """UDP-based controller for mioXL device"""
    
    def __init__(self, device_ip: str, device_port: int = 5006):
        self.device_ip = device_ip
        self.device_port = device_port
        self.session_active = False
        self.ssrc = None
        self.token = None
        self.device_name = None
        self.socket = None
        self.listen_thread = None
        self.running = False
        self.midi_callback: Optional[Callable] = None
    
    def connect(self, session_name: str = "mioXLController") -> bool:
        """
        Establish AppleMIDI session with device
        
        Args:
            session_name: Name for this session
            
        Returns:
            True if connected successfully
        """
        print(f"🔌 Connecting to {self.device_ip}:{self.device_port}")
        
        try:
            # Create UDP socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.settimeout(5)
            
            # Build invitation packet
            signature = b'\xff\xff'
            command = b'IN'
            protocol_version = struct.pack('!I', 2)
            initiator_token = struct.pack('!I', 0x12345678)
            ssrc = struct.pack('!I', 0x87654321)
            name_bytes = session_name.encode('ascii') + b'\x00'
            
            packet = signature + command + protocol_version + initiator_token + ssrc + name_bytes
            
            # Send invitation
            self.socket.sendto(packet, (self.device_ip, self.device_port))
            
            # Wait for acceptance
            data, addr = self.socket.recvfrom(1024)
            
            if len(data) >= 16 and data[0:2] == b'\xff\xff':
                cmd = data[2:4].decode('ascii', errors='ignore')
                
                if cmd == 'OK':
                    # Parse response
                    proto_ver = struct.unpack('!I', data[4:8])[0]
                    self.token = struct.unpack('!I', data[8:12])[0]
                    self.ssrc = struct.unpack('!I', data[12:16])[0]
                    
                    if len(data) > 16:
                        self.device_name = data[16:].decode('ascii', errors='ignore').rstrip('\x00')
                    
                    self.session_active = True
                    
                    print(f"✅ Connected to: {self.device_name}")
                    print(f"   SSRC: 0x{self.ssrc:08x}")
                    print(f"   Token: 0x{self.token:08x}")
                    
                    # Start listener thread
                    self.running = True
                    self.socket.settimeout(0.1)  # Non-blocking with short timeout
                    self.listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
                    self.listen_thread.start()
                    
                    return True
                
                elif cmd == 'NO':
                    print(f"❌ Connection rejected by device")
                    return False
            
        except socket.timeout:
            print(f"❌ Connection timeout - device did not respond")
            return False
        
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False
        
        return False
    
    def disconnect(self):
        """End session and close connection"""
        if self.session_active:
            print(f"👋 Disconnecting from {self.device_name}")
            
            # Send end session
            signature = b'\xff\xff'
            command = b'BY'
            protocol_version = struct.pack('!I', 2)
            initiator_token = struct.pack('!I', 0x12345678)
            ssrc = struct.pack('!I', 0x87654321)
            
            packet = signature + command + protocol_version + initiator_token + ssrc
            
            try:
                self.socket.sendto(packet, (self.device_ip, self.device_port))
            except:
                pass
            
            self.running = False
            if self.listen_thread:
                self.listen_thread.join(timeout=1)
            
            self.session_active = False
        
        if self.socket:
            self.socket.close()
            self.socket = None
    
    def _listen_loop(self):
        """Background thread to receive MIDI data"""
        while self.running:
            try:
                data, addr = self.socket.recvfrom(1024)
                
                if data:
                    self._handle_received_data(data, addr)
            
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"⚠ Receive error: {e}")
                break
    
    def _handle_received_data(self, data: bytes, addr: tuple):
        """
        Handle received RTP-MIDI or AppleMIDI data
        
        Args:
            data: Received packet data
            addr: Sender address
        """
        # Check if it's AppleMIDI control message
        if len(data) >= 4 and data[0:2] == b'\xff\xff':
            cmd = data[2:4].decode('ascii', errors='ignore')
            
            if cmd == 'CK':
                # Synchronization packet
                pass  # Can implement timestamp sync if needed
            
            elif cmd == 'RS':
                # Receiver feedback
                pass
            
            elif cmd == 'BY':
                # Session ended by device
                print(f"⚠ Device ended session")
                self.session_active = False
        
        # Check if it's RTP-MIDI data
        elif len(data) >= 12:
            # RTP header (simplified parsing)
            vpxcc = data[0]
            v = (vpxcc >> 6) & 0x03
            
            if v == 2:  # RTP version 2
                # This is RTP-MIDI data
                payload_type = data[1] & 0x7F
                sequence = struct.unpack('!H', data[2:4])[0]
                timestamp = struct.unpack('!I', data[4:8])[0]
                ssrc = struct.unpack('!I', data[8:12])[0]
                
                # MIDI payload starts at byte 12
                midi_data = data[12:]
                
                if midi_data and self.midi_callback:
                    self.midi_callback(midi_data)
                elif midi_data:
                    self._print_midi_data(midi_data)
    
    def _print_midi_data(self, midi_data: bytes):
        """Print received MIDI data"""
        # Parse MIDI command list
        if len(midi_data) < 1:
            return
        
        # RTP-MIDI payload header
        flags = midi_data[0]
        has_journal = (flags & 0x80) != 0
        
        print(f"📨 MIDI Data: {midi_data.hex()}")
        
        # Parse MIDI messages (simplified)
        i = 1
        while i < len(midi_data):
            status = midi_data[i]
            
            if status >= 0x80:  # Status byte
                if status >= 0xF0:
                    print(f"   System: 0x{status:02x}")
                    i += 1
                elif status >= 0xE0:
                    if i + 2 < len(midi_data):
                        print(f"   Pitch Bend: ch{status&0x0F} = {midi_data[i+1]} {midi_data[i+2]}")
                        i += 3
                elif status >= 0xD0:
                    if i + 1 < len(midi_data):
                        print(f"   Channel Pressure: ch{status&0x0F} = {midi_data[i+1]}")
                        i += 2
                elif status >= 0xC0:
                    if i + 1 < len(midi_data):
                        print(f"   Program Change: ch{status&0x0F} = {midi_data[i+1]}")
                        i += 2
                elif status >= 0xB0:
                    if i + 2 < len(midi_data):
                        print(f"   Control Change: ch{status&0x0F} CC{midi_data[i+1]} = {midi_data[i+2]}")
                        i += 3
                elif status >= 0xA0:
                    if i + 2 < len(midi_data):
                        print(f"   Poly Pressure: ch{status&0x0F} note{midi_data[i+1]} = {midi_data[i+2]}")
                        i += 3
                elif status >= 0x90:
                    if i + 2 < len(midi_data):
                        vel = midi_data[i+2]
                        note_type = "Note On" if vel > 0 else "Note Off"
                        print(f"   {note_type}: ch{status&0x0F} note{midi_data[i+1]} vel{vel}")
                        i += 3
                elif status >= 0x80:
                    if i + 2 < len(midi_data):
                        print(f"   Note Off: ch{status&0x0F} note{midi_data[i+1]} vel{midi_data[i+2]}")
                        i += 3
                else:
                    i += 1
            else:
                i += 1
    
    def send_midi(self, midi_data: bytes):
        """
        Send MIDI data to device
        
        Args:
            midi_data: MIDI message bytes
        """
        if not self.session_active:
            print("❌ Not connected to device")
            return
        
        # Build RTP-MIDI packet
        # RTP header
        vpxcc = 0x80  # V=2, P=0, X=0, CC=0
        mpt = 0x61    # M=0, PT=97 (dynamic payload type for MIDI)
        sequence = 1  # Simplified - should increment
        timestamp = int(time.time() * 1000) & 0xFFFFFFFF
        ssrc = 0x87654321
        
        rtp_header = struct.pack('!BBHII',
            vpxcc,
            mpt,
            sequence,
            timestamp,
            ssrc
        )
        
        # MIDI command section
        midi_flags = 0x00  # No journal
        midi_payload = bytes([midi_flags]) + midi_data
        
        packet = rtp_header + midi_payload
        
        try:
            self.socket.sendto(packet, (self.device_ip, self.device_port))
            print(f"📤 Sent MIDI: {midi_data.hex()}")
        except Exception as e:
            print(f"❌ Send error: {e}")
    
    def send_note_on(self, channel: int = 0, note: int = 60, velocity: int = 100):
        """Send Note On message"""
        midi_data = bytes([0x90 | (channel & 0x0F), note & 0x7F, velocity & 0x7F])
        self.send_midi(midi_data)
    
    def send_note_off(self, channel: int = 0, note: int = 60, velocity: int = 0):
        """Send Note Off message"""
        midi_data = bytes([0x80 | (channel & 0x0F), note & 0x7F, velocity & 0x7F])
        self.send_midi(midi_data)
    
    def send_cc(self, channel: int = 0, controller: int = 1, value: int = 64):
        """Send Control Change message"""
        midi_data = bytes([0xB0 | (channel & 0x0F), controller & 0x7F, value & 0x7F])
        self.send_midi(midi_data)
    
    def send_program_change(self, channel: int = 0, program: int = 0):
        """Send Program Change message"""
        midi_data = bytes([0xC0 | (channel & 0x0F), program & 0x7F])
        self.send_midi(midi_data)
    
    def query_presets(self) -> dict:
        """
        Query device for preset information via SysEx
        Note: This sends SysEx queries and listens for responses
        """
        if not self.session_active:
            print("❌ Not connected to device")
            return {}
        
        print("\n📋 Querying device presets...")
        
        # iConnectivity manufacturer ID: 0x00 0x01 0x73
        # Try sending SysEx query for presets
        
        # Query current preset (SysEx)
        sysex_query = bytes([
            0xF0,           # SysEx start
            0x00, 0x01, 0x73,  # iConnectivity manufacturer ID
            0x7D,           # Message class
            # Query for preset information
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  # Device ID (broadcast)
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00,        # Foo ID
            0x00, 0x01,     # Transaction ID
            0x00, 0x07,     # Length
            0x03,           # Flags (QUERY)
            0x03,           # Command (PRESET)
            0x01,           # Args
            0x04, 0x01, 0x01, 0x01,  # Query current preset
            0x6C,           # Checksum
            0xF7            # SysEx end
        ])
        
        # Store responses
        self.preset_responses = []
        
        # Send query
        try:
            self.socket.sendto(sysex_query, (self.device_ip, self.device_port))
            print("  ⏳ Waiting for response...")
            
            # Wait a bit for response
            time.sleep(2)
            
            # Check if we got any SysEx responses in our listener
            if self.preset_responses:
                print(f"  ✓ Received {len(self.preset_responses)} response(s)")
                return {"presets": self.preset_responses}
            else:
                print("  ℹ No SysEx response received")
                print("  💡 Device may not support SysEx over network")
                print("     Presets can typically only be queried via USB connection")
                return {}
        
        except Exception as e:
            print(f"  ❌ Query error: {e}")
            return {}


def interactive_mode(controller: MioXLController):
    """Interactive command mode"""
    print("\n" + "="*70)
    print("Interactive Mode - Commands:")
    print("="*70)
    print("  note <channel> <note> <velocity>  - Send Note On")
    print("  cc <channel> <controller> <value> - Send Control Change")
    print("  pc <channel> <program>            - Send Program Change")
    print("  presets                            - Query device presets")
    print("  listen                             - Listen for incoming MIDI")
    print("  help                               - Show this help")
    print("  quit                               - Exit")
    print("="*70 + "\n")
    
    while controller.session_active:
        try:
            cmd = input("mioXL> ").strip().split()
            
            if not cmd:
                continue
            
            if cmd[0] == 'quit':
                break
            
            elif cmd[0] == 'help':
                print("Commands: note, cc, pc, listen, quit")
            
            elif cmd[0] == 'note' and len(cmd) >= 4:
                ch, note, vel = int(cmd[1]), int(cmd[2]), int(cmd[3])
                controller.send_note_on(ch, note, vel)
                time.sleep(0.1)
                controller.send_note_off(ch, note, 0)
            
            elif cmd[0] == 'cc' and len(cmd) >= 4:
                ch, cc_num, val = int(cmd[1]), int(cmd[2]), int(cmd[3])
                controller.send_cc(ch, cc_num, val)
            
            elif cmd[0] == 'pc' and len(cmd) >= 3:
                ch, prog = int(cmd[1]), int(cmd[2])
                controller.send_program_change(ch, prog)
            
            elif cmd[0] == 'listen':
                print("Listening for MIDI (Ctrl+C to stop)...")
                try:
                    while True:
                        time.sleep(0.1)
                except KeyboardInterrupt:
                    print("\nStopped listening")
            
            elif cmd[0] == 'presets':
                controller.query_presets()
            
            else:
                print("Unknown command. Type 'help' for commands.")
        
        except KeyboardInterrupt:
            print("\n")
            break
        except Exception as e:
            print(f"Error: {e}")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="UDP controller for mioXL device")
    parser.add_argument("ip", help="Device IP address")
    parser.add_argument("--port", type=int, default=5006, help="Device port (default: 5006)")
    parser.add_argument("--name", default="mioXLController", help="Session name")
    parser.add_argument("--test", action="store_true", help="Run test sequence")
    
    args = parser.parse_args()
    
    print("\n🎹 mioXL UDP Controller")
    print("="*70 + "\n")
    
    controller = MioXLController(args.ip, args.port)
    
    if controller.connect(args.name):
        
        if args.test:
            # Test sequence
            print("\n🧪 Running test sequence...")
            time.sleep(1)
            
            print("  Testing Note On/Off...")
            controller.send_note_on(0, 60, 100)
            time.sleep(0.5)
            controller.send_note_off(0, 60, 0)
            
            print("  Testing CC...")
            controller.send_cc(0, 1, 64)
            
            print("  Test complete!")
            time.sleep(1)
        
        else:
            # Interactive mode
            interactive_mode(controller)
        
        controller.disconnect()
    
    print("\n👋 Goodbye!\n")


if __name__ == "__main__":
    main()
