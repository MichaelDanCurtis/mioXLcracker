#!/usr/bin/env python3
"""
mio XL Network Query Tool
Sends RTP-MIDI (AppleMIDI) packets to discover device name and info
"""

import socket
import struct
import sys


def send_applemidi_invitation(target_ip: str, port: int = 5004, session_name: str = "mioXLQuery"):
    """
    Send AppleMIDI session invitation to device.
    
    AppleMIDI Protocol Format:
    - Signature: 0xFFFF (2 bytes)
    - Command: 'IN' for invitation (2 bytes)
    - Protocol Version: 2 (4 bytes)
    - Initiator Token: Random (4 bytes)
    - SSRC: Synchronization Source (4 bytes)
    - Name: Session name (variable, null-terminated)
    
    Args:
        target_ip: IP address of device
        port: RTP-MIDI control port (default 5004)
        session_name: Name to identify this session
    
    Returns:
        Device information dict or None
    """
    print("=" * 70)
    print(f"Querying mio XL Device at {target_ip}:{port}")
    print("=" * 70)
    
    try:
        # Create UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(5)  # 5 second timeout
        
        # Build AppleMIDI Invitation packet
        signature = b'\xff\xff'                          # AppleMIDI signature
        command = b'IN'                                  # Invitation command
        protocol_version = struct.pack('!I', 2)          # Protocol version 2
        initiator_token = struct.pack('!I', 0x12345678)  # Our token
        ssrc = struct.pack('!I', 0x87654321)             # Our SSRC
        name_bytes = session_name.encode('ascii') + b'\x00'  # Null-terminated name
        
        invitation_packet = signature + command + protocol_version + initiator_token + ssrc + name_bytes
        
        print(f"\n→ Sending AppleMIDI Invitation Packet")
        print(f"   Packet size: {len(invitation_packet)} bytes")
        print(f"   Hex: {invitation_packet.hex()}")
        print(f"   Session name: '{session_name}'")
        
        # Send invitation
        sock.sendto(invitation_packet, (target_ip, port))
        print(f"   ✓ Packet sent to {target_ip}:{port}")
        
        # Wait for response
        print(f"\n← Waiting for response (timeout: 5s)...")
        
        try:
            data, addr = sock.recvfrom(1024)
            
            print(f"   ✓ Received {len(data)} bytes from {addr[0]}:{addr[1]}")
            print(f"   Hex: {data.hex()}")
            
            # Parse response
            if len(data) >= 4:
                response_sig = data[0:2]
                response_cmd = data[2:4]
                
                print(f"\n📦 Parsing Response:")
                print(f"   Signature: {response_sig.hex()} {'✓ Valid' if response_sig == b'\\xff\\xff' else '✗ Invalid'}")
                print(f"   Command: {response_cmd.decode('ascii', errors='ignore')}")
                
                # Check if it's an acceptance or rejection
                if response_sig == b'\xff\xff':
                    cmd_str = response_cmd.decode('ascii', errors='ignore')
                    
                    if cmd_str == 'OK':
                        print(f"   ✓ Invitation ACCEPTED")
                        
                        # Parse the rest of the packet
                        if len(data) >= 16:
                            proto_ver = struct.unpack('!I', data[4:8])[0]
                            resp_token = struct.unpack('!I', data[8:12])[0]
                            resp_ssrc = struct.unpack('!I', data[12:16])[0]
                            
                            print(f"   Protocol Version: {proto_ver}")
                            print(f"   Responder Token: 0x{resp_token:08x}")
                            print(f"   Responder SSRC: 0x{resp_ssrc:08x}")
                            
                            # Extract device name (everything after byte 16)
                            if len(data) > 16:
                                device_name_bytes = data[16:]
                                device_name = device_name_bytes.decode('ascii', errors='ignore').rstrip('\x00')
                                
                                print(f"\n{'=' * 70}")
                                print(f"🎹 DEVICE NAME: {device_name}")
                                print(f"{'=' * 70}")
                                
                                return {
                                    'name': device_name,
                                    'ip': target_ip,
                                    'port': port,
                                    'protocol_version': proto_ver,
                                    'ssrc': resp_ssrc,
                                    'token': resp_token
                                }
                    
                    elif cmd_str == 'NO':
                        print(f"   ✗ Invitation REJECTED")
                        
                        # Parse rejection reason if available
                        if len(data) >= 16:
                            proto_ver = struct.unpack('!I', data[4:8])[0]
                            resp_token = struct.unpack('!I', data[8:12])[0]
                            resp_ssrc = struct.unpack('!I', data[12:16])[0]
                            
                            print(f"   Protocol Version: {proto_ver}")
                            print(f"   Token: 0x{resp_token:08x}")
                            print(f"   SSRC: 0x{resp_ssrc:08x}")
                    
                    else:
                        print(f"   ⚠ Unknown response command: {cmd_str}")
                
                else:
                    print(f"   ✗ Invalid AppleMIDI signature")
            
            else:
                print(f"   ✗ Response too short ({len(data)} bytes)")
        
        except socket.timeout:
            print(f"   ✗ No response received (timeout)")
            print(f"\n💡 Troubleshooting:")
            print(f"   - Verify device is powered on")
            print(f"   - Check network connectivity (ping {target_ip})")
            print(f"   - Ensure device has network MIDI enabled")
            print(f"   - Verify IP address is correct")
        
        sock.close()
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    return None


def query_device_with_retries(target_ip: str, max_attempts: int = 3):
    """
    Query device with multiple retry attempts.
    
    Args:
        target_ip: IP address of device
        max_attempts: Maximum number of attempts
    
    Returns:
        Device information dict or None
    """
    for attempt in range(1, max_attempts + 1):
        if attempt > 1:
            print(f"\n\n🔄 Retry attempt {attempt}/{max_attempts}")
        
        result = send_applemidi_invitation(target_ip, port=5004, session_name=f"Query{attempt}")
        
        if result:
            return result
        
        if attempt < max_attempts:
            import time
            time.sleep(1)
    
    print(f"\n\n✗ Failed after {max_attempts} attempts")
    return None


def main():
    """Main entry point"""
    target_ip = sys.argv[1] if len(sys.argv) > 1 else "192.168.1.199"
    
    print("\n🎹 mio XL Network Query Tool")
    print(f"Target: {target_ip}\n")
    
    result = query_device_with_retries(target_ip, max_attempts=3)
    
    if result:
        print(f"\n\n✅ SUCCESS!")
        print(f"\nDevice Information:")
        print(f"  Name: {result['name']}")
        print(f"  IP: {result['ip']}")
        print(f"  Port: {result['port']}")
        print(f"  Protocol: AppleMIDI v{result['protocol_version']}")
        print(f"  SSRC: 0x{result['ssrc']:08x}")
    else:
        print(f"\n\n❌ FAILED to identify device")
    
    print("\n")


if __name__ == "__main__":
    main()
