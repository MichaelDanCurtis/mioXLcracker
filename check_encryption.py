import sys
import struct

def analyze_entropy(filename):
    print(f"Analyzing entropy of: {filename}")
    with open(filename, 'rb') as f:
        data = f.read()
    
    # Calculate entropy of 256-byte blocks
    import math
    
    def entropy(data_chunk):
        if not data_chunk:
            return 0
        entropy = 0
        for x in range(256):
            p_x = float(data_chunk.count(x))/len(data_chunk)
            if p_x > 0:
                entropy += - p_x*math.log(p_x, 2)
        return entropy

    # Check first few blocks
    print(f"First 1KB Entropy: {entropy(data[:1024])}")
    print(f"Middle 1KB Entropy: {entropy(data[len(data)//2:len(data)//2+1024])}")
    
    # Check for common compression/encryption headers
    # ZIP, GZIP, 7Z, etc.
    print(f"Header: {data[:16].hex()}")
    
    # Check for repeating patterns (padding)
    print(f"Trailing bytes: {data[-16:].hex()}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        analyze_entropy(sys.argv[1])
