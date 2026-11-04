import sys
import struct

def read_variable_length(data, offset):
    value = 0
    bytes_read = 0
    while True:
        byte = data[offset + bytes_read]
        bytes_read += 1
        value = (value << 7) | (byte & 0x7F)
        if not (byte & 0x80):
            break
    return value, bytes_read

def parse_midi_file(filename):
    print(f"Parsing MIDI file: {filename}")
    try:
        with open(filename, 'rb') as f:
            data = f.read()
    except FileNotFoundError:
        print("File not found.")
        return

    if data[0:4] != b'MThd':
        print("Not a valid MIDI file (missing MThd header).")
        return

    header_len = struct.unpack('>I', data[4:8])[0]
    format_type, num_tracks, time_division = struct.unpack('>HHH', data[8:8+header_len])
    print(f"Format: {format_type}, Tracks: {num_tracks}, Time Division: {time_division}")

    offset = 8 + header_len
    
    for track_idx in range(num_tracks):
        if offset >= len(data):
            break
            
        if data[offset:offset+4] != b'MTrk':
            print(f"Expected MTrk at {hex(offset)}, found {data[offset:offset+4]}")
            break
            
        track_len = struct.unpack('>I', data[offset+4:offset+8])[0]
        print(f"\nTrack {track_idx} (Length: {track_len} bytes)")
        
        track_end = offset + 8 + track_len
        curr = offset + 8
        
        while curr < track_end:
            # Read Delta Time
            delta_time, bytes_read = read_variable_length(data, curr)
            curr += bytes_read
            
            if curr >= track_end:
                break
                
            # Read Event Type
            status = data[curr]
            
            # SysEx Event (F0)
            if status == 0xF0:
                curr += 1
                length, bytes_read = read_variable_length(data, curr)
                curr += bytes_read
                sysex_data = data[curr:curr+length]
                curr += length
                
                print(f"  [SysEx] Len={length}")
                print(f"    Raw: F0 {sysex_data.hex()}")
                
                # Check for iConnectivity Header: F0 00 01 73 7D
                if sysex_data.startswith(b'\x00\x01\x73\x7D'):
                    print("    Type: iConnectivity Command")
                    # Try to decode command bytes
                    # F0 00 01 73 7D [Body] F7
                    # Body usually starts with some padding or transaction ID?
                    # Let's just print the first 16 bytes of the body
                    print(f"    Body: {sysex_data[4:20].hex()}...")
            
            # Meta Event (FF)
            elif status == 0xFF:
                curr += 1
                meta_type = data[curr]
                curr += 1
                length, bytes_read = read_variable_length(data, curr)
                curr += bytes_read
                meta_data = data[curr:curr+length]
                curr += length
                # print(f"  [Meta] Type={hex(meta_type)} Len={length}")
                
            # MIDI Event (8x-Ex)
            elif 0x80 <= status <= 0xEF:
                curr += 1
                # Determine length based on status
                # Note Off, Note On, Poly Key Pressure, Control Change, Pitch Bend = 2 bytes
                # Program Change, Channel Pressure = 1 byte
                high_nibble = status & 0xF0
                if high_nibble in [0xC0, 0xD0]:
                    curr += 1
                else:
                    curr += 2
            else:
                # Running status or unknown?
                # For simplicity in this DFU parser, we might skip or break
                # print(f"  [Unknown] Status={hex(status)} at {hex(curr)}")
                curr += 1
                
        offset = track_end

if __name__ == "__main__":
    if len(sys.argv) > 1:
        parse_midi_file(sys.argv[1])
    else:
        print("Usage: python3 parse_midi_firmware.py <file.mid>")
