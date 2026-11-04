import re

def analyze_strings(filename):
    with open(filename, 'r') as f:
        content = f.read()
        
    # Extract hex strings
    hex_strings = re.findall(r'Raw: ([0-9a-fA-F]+)', content)
    
    print(f"Analyzing {len(hex_strings)} messages for ASCII...")
    
    for i, h in enumerate(hex_strings):
        try:
            b = bytes.fromhex(h)
            # Filter for printable ASCII
            chars = []
            for byte in b:
                if 32 <= byte <= 126:
                    chars.append(chr(byte))
                else:
                    chars.append('.')
            s = "".join(chars)
            
            # Check if it contains a significant string (len > 3)
            clean_s = s.replace('.', '')
            if len(clean_s) > 3:
                print(f"Msg {i}: {s}")
        except:
            pass

if __name__ == "__main__":
    analyze_strings("firmware_sysex.txt")
