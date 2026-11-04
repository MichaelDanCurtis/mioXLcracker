from scapy.all import sniff, UDP, Raw
import struct
import sys

def parse_packet(pkt):
    if UDP in pkt and Raw in pkt:
        payload = bytes(pkt[Raw].load)
        src = pkt[UDP].sport
        dst = pkt[UDP].dport
        
        # RTP-MIDI (0x80 0x61...)
        if len(payload) > 12 and payload[1] & 0x7F == 0x61:
            ssrc = struct.unpack('>I', payload[8:12])[0]
            # Look for SysEx
            try:
                idx = payload.index(b'\xf0')
                end = payload.index(b'\xf7', idx)
                sysex = payload[idx:end+1]
                
                # Decode ASCII
                ascii_str = ''.join(chr(b) for b in sysex if 32 <= b <= 126)
                print(f"[UDP {src}->{dst}] SSRC={hex(ssrc)} | ASCII: {ascii_str}")
                # print(f"    Raw: {sysex.hex()}")
            except ValueError:
                pass
        
        # AppleMIDI (FF FF ...)
        elif len(payload) >= 2 and payload[0:2] == b'\xff\xff':
             cmd = payload[2:4].decode('ascii', errors='ignore')
             print(f"[UDP {src}->{dst}] AppleMIDI {cmd}")

print("Monitoring UDP 5003 traffic... (Press Ctrl+C to stop)")
sniff(filter="udp port 5003", prn=parse_packet, store=0)
