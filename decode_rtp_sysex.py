from scapy.all import rdpcap, UDP, Raw
import struct

def parse_rtp_midi(payload):
    if len(payload) < 12:
        return None
    
    # RTP Header (12 bytes)
    v_p_x_cc = payload[0]
    m_pt = payload[1]
    seq = struct.unpack('>H', payload[2:4])[0]
    timestamp = struct.unpack('>I', payload[4:8])[0]
    ssrc = struct.unpack('>I', payload[8:12])[0]
    
    midi_data = payload[12:]
    
    # MIDI Command Section
    # First byte: B J Z P Len(4)
    if len(midi_data) == 0:
        return None
        
    header = midi_data[0]
    b_flag = (header >> 7) & 1
    j_flag = (header >> 6) & 1
    z_flag = (header >> 5) & 1
    p_flag = (header >> 4) & 1
    length = header & 0x0F
    
    # If B=1, length is encoded in octets? 
    # Actually, for long SysEx, the length handling is specific.
    # But let's just look for F0 ... F7 in the raw data for now.
    
    try:
        sysex_start = midi_data.index(b'\xf0')
        sysex_end = midi_data.index(b'\xf7', sysex_start)
        return midi_data[sysex_start:sysex_end+1]
    except ValueError:
        return None

def analyze_pcap(filename):
    packets = rdpcap(filename)
    print(f"Analyzing {len(packets)} packets from {filename}...")
    
    with open("decoded_sysex.txt", "w") as f:
        for i, pkt in enumerate(packets):
            if UDP in pkt and Raw in pkt:
                payload = bytes(pkt[Raw].load)
                
                # Check for AppleMIDI Control (FF FF)
                if len(payload) >= 2 and payload[0:2] == b'\xff\xff':
                    cmd = payload[2:4].decode('ascii', errors='ignore')
                    src = pkt[UDP].sport
                    dst = pkt[UDP].dport
                    direction = "HOST -> DEVICE" if dst == 5003 else "DEVICE -> HOST"
                    f.write(f"\nPacket {i} ({direction}) Src={src} Dst={dst} AppleMIDI {cmd}:\n")
                    f.write(f"  Hex: {payload.hex()}\n")
                    if cmd == 'IN':
                        f.write(f"  Name: {payload[16:].decode('ascii', errors='ignore')}\n")
                
                # Check for RTP-MIDI (Payload Type 97 = 0x61)
                elif len(payload) > 12 and payload[1] & 0x7F == 0x61:
                    ssrc = struct.unpack('>I', payload[8:12])[0]
                    sysex = parse_rtp_midi(payload)
                    if sysex:
                        src = pkt[UDP].sport
                        dst = pkt[UDP].dport
                        direction = "HOST -> DEVICE" if dst == 5003 else "DEVICE -> HOST"
                        
                        f.write(f"\nPacket {i} ({direction}) Src={src} Dst={dst} SSRC={hex(ssrc)}:\n")
                        f.write(f"  SysEx: {sysex.hex()}\n")
                        
                        # Decode iConnectivity SysEx
                        # F0 00 01 73 7D ...
                        if sysex.startswith(b'\xf0\x00\x01\x73\x7d'):
                            # Skip header (5 bytes)
                            data = sysex[5:]
                            f.write(f"  Data:  {data.hex()}\n")
                            
                            # Try to interpret ASCII
                            ascii_str = ''.join(chr(b) for b in data if 32 <= b <= 126)
                            if ascii_str:
                                f.write(f"  ASCII: {ascii_str}\n")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        analyze_pcap(sys.argv[1])
    else:
        print("Usage: python3 decode_rtp_sysex.py <file.pcap>")
