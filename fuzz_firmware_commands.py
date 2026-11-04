import socket
import time
import sys

IP = "192.168.1.199"
PORT = 5003

def parse_hex_string(hex_str):
    return bytes.fromhex(hex_str)

def load_messages(filename):
    with open(filename, 'r') as f:
        lines = f.readlines()
    messages = []
    for line in lines:
        if "Raw:" in line:
            raw = line.split("Raw:")[1].strip()
            messages.append(parse_hex_string(raw))
    return messages

def send_udp(sock, ip, port, data):
    # print(f"Sending {len(data)} bytes to {ip}:{port}")
    sock.sendto(data, (ip, port))

def listen(sock, duration=0.1):
    end = time.time() + duration
    while time.time() < end:
        try:
            data, addr = sock.recvfrom(1024)
            print(f"RESPONSE from {addr}: {data.hex()}")
            return True
        except socket.timeout:
            pass
    return False

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', 0))
    sock.settimeout(0.1)
    
    print(f"Loading messages from firmware_sysex.txt...")
    msgs = load_messages("firmware_sysex.txt")
    print(f"Loaded {len(msgs)} messages.")
    
    # Filter for short messages (likely control commands)
    short_msgs = [m for m in msgs if len(m) < 50]
    print(f"Found {len(short_msgs)} short messages.")
    
    print(f"Fuzzing Ports 5003-5006 with short messages...")
    
    ports = [5003, 5004, 5005, 5006]
    
    for i, msg in enumerate(short_msgs):
        for port in ports:
            # Send Raw
            send_udp(sock, IP, port, msg)
            if listen(sock, 0.02):
                print(f"  -> Triggered by Message {i} (Len {len(msg)}) on Port {port}: {msg.hex()}")
                # break loop? No, keep going to see if others respond
                
            # Send Modified (00 00 instead of 00 0E)
            if len(msg) > 7 and msg[5] == 0x00 and msg[6] == 0x0E:
                mod_msg = bytearray(msg)
                mod_msg[6] = 0x00 # Change 0E to 00
                send_udp(sock, IP, port, mod_msg)
                if listen(sock, 0.02):
                    print(f"  -> Triggered by Modified Message {i} (Len {len(msg)}) on Port {port}: {mod_msg.hex()}")

                
    print("Done.")
    sock.close()

if __name__ == "__main__":
    main()
