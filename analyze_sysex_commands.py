import sys

def parse_hex_string(hex_str):
    return bytes.fromhex(hex_str)

def analyze_firmware_sysex(filename):
    with open(filename, 'r') as f:
        lines = f.readlines()

    messages = []
    current_raw = ""
    
    for line in lines:
        if "Raw:" in line:
            current_raw = line.split("Raw:")[1].strip()
            messages.append(parse_hex_string(current_raw))

    print(f"Found {len(messages)} SysEx messages.")
    
    # Group by length
    by_length = {}
    for msg in messages:
        l = len(msg)
        if l not in by_length:
            by_length[l] = []
        by_length[l].append(msg)
        
    print("\nMessages by Length:")
    for l in sorted(by_length.keys()):
        print(f"Length {l}: {len(by_length[l])} messages")
        # Print the first one of this length as example
        print(f"  Example: {by_length[l][0].hex()}")

    # Analyze headers (first 21 bytes)
    print("\nHeader Analysis (first 21 bytes):")
    headers = {}
    for msg in messages:
        if len(msg) >= 21:
            hdr = msg[:21]
            if hdr not in headers:
                headers[hdr] = 0
            headers[hdr] += 1
            
    for hdr, count in headers.items():
        print(f"  {hdr.hex()} : {count} times")

    # Analyze the "Command" byte (byte 21, index 21?)
    # Based on previous observation: F0 00 01 73 7D 00 0E ... 00 08 7F 7F ...
    # The byte after the 14 zeros seems to be 08 or 0C.
    # Let's look at bytes 19, 20, 21.
    
    print("\nPayload Start Analysis (bytes 19-25):")
    payload_starts = {}
    for msg in messages:
        if len(msg) > 25:
            chunk = msg[19:25]
            if chunk not in payload_starts:
                payload_starts[chunk] = 0
            payload_starts[chunk] += 1
            
    for chunk, count in payload_starts.items():
        print(f"  {chunk.hex()} : {count} times")

if __name__ == "__main__":
    analyze_firmware_sysex("firmware_sysex.txt")
