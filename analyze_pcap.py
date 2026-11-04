from scapy.all import rdpcap, Raw
import sys

def analyze(filename):
    with open("analysis_result.txt", "w") as f:
        f.write(f"Reading {filename}...\n")
        try:
            packets = rdpcap(filename)
        except Exception as e:
            f.write(f"Error reading pcap: {e}\n")
            return

        f.write(f"Total packets: {len(packets)}\n")
        
        found_beer = False
        for i, pkt in enumerate(packets):
            if Raw in pkt:
                payload = bytes(pkt[Raw].load)
                if b'beer1' in payload:
                    f.write(f"Packet {i}: FOUND 'beer1'\n")
                    f.write(f"{payload.hex()}\n")
                    f.write(f"{payload}\n")
                    found_beer = True
                
                # Also look for large SysEx
                if payload.startswith(b'\xf0') and len(payload) > 10:
                    f.write(f"Packet {i}: SysEx found ({len(payload)} bytes)\n")
                    f.write(f"{payload[:20].hex()}...\n")

        if not found_beer:
            f.write("Did not find 'beer1' in any packet.\n")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        analyze(sys.argv[1])
    else:
        print("Usage: python3 analyze_pcap.py <file.pcap>")
