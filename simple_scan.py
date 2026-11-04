import socket, sys, struct

IP = "192.168.1.199"
PORTS = [5003, 5004, 5005, 5006]

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(1.0)

for port in PORTS:
    print(f"Scanning {port}...")
    # AppleMIDI Invitation
    pkt = b'\xff\xff' + b'IN' + struct.pack('!III', 2, 0x12345678, 0x87654321) + b'Probe\x00'
    sock.sendto(pkt, (IP, port))
    try:
        data, addr = sock.recvfrom(1024)
        print(f"  Response from {port}: {data.hex()}")
        if len(data) > 4:
            print(f"  Type: {data[2:4]}")
    except socket.timeout:
        print(f"  No response from {port}")

sock.close()
