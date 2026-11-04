import sys
import re

def analyze_firmware(filename):
    print(f"Analyzing firmware: {filename}")
    
    try:
        with open(filename, 'rb') as f:
            data = f.read()
    except FileNotFoundError:
        print("File not found.")
        return

    print(f"Total size: {len(data)} bytes")

    # 1. Search for SysEx Header (F0 00 01 73 7D)
    # This confirms we are looking at the code that handles these messages
    sysex_header = b'\xF0\x00\x01\x73\x7D'
    header_offsets = [i for i in range(len(data)) if data.startswith(sysex_header, i)]
    print(f"\n[+] Found {len(header_offsets)} SysEx headers (F0 00 01 73 7D):")
    for off in header_offsets[:10]:
        print(f"    Offset: {hex(off)}")
        # Print context around it
        context = data[off:off+32]
        print(f"    Context: {context.hex()}")

    # 2. Extract Strings (ASCII and UTF-16)
    # Look for interesting keywords: "Preset", "UDP", "RTP", "Error", "NO"
    print("\n[+] Extracting interesting strings...")
    
    # Simple ASCII extraction (4+ chars)
    ascii_strings = re.findall(b'[ -~]{4,}', data)
    
    keywords = [b'Preset', b'UDP', b'RTP', b'Apple', b'Session', b'Error', b'Debug', b'beer', b'mioXL']
    
    found_keywords = {}
    
    for s in ascii_strings:
        try:
            decoded = s.decode('ascii')
            for k in keywords:
                if k.decode('ascii').lower() in decoded.lower():
                    if k not in found_keywords:
                        found_keywords[k] = []
                    if len(found_keywords[k]) < 10: # Limit output
                        found_keywords[k].append(decoded)
        except:
            pass

    for k, v in found_keywords.items():
        print(f"  Matches for '{k.decode()}':")
        for match in v:
            print(f"    {match}")

    # 3. Look for the "NO" response packet (FFFF ... NO)
    # The rejection packet was: FF FF 4E 4F (NO)
    no_resp = b'\xFF\xFF\x4E\x4F'
    no_offsets = [i for i in range(len(data)) if data.startswith(no_resp, i)]
    print(f"\n[+] Found {len(no_offsets)} 'AppleMIDI NO' signatures:")
    for off in no_offsets:
        print(f"    Offset: {hex(off)}")

    # 4. Look for the Command Bytes we saw: 03 03 02 05 04 01
    # This is the "Get Preset Name" command sequence
    cmd_seq = b'\x03\x03\x02\x05\x04\x01'
    cmd_offsets = [i for i in range(len(data)) if data.startswith(cmd_seq, i)]
    print(f"\n[+] Found {len(cmd_offsets)} Command Sequences (03 03 02...):")
    for off in cmd_offsets:
        print(f"    Offset: {hex(off)}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        analyze_firmware(sys.argv[1])
    else:
        print("Usage: python3 analyze_firmware.py <firmware.bin>")
