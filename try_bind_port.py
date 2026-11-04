import socket
import sys
import struct
import time

IP = "192.168.1.199"
TARGET_PORT = 5003

def try_connect(local_port):
    print(f"Trying to bind to local port {local_port}...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.bind(('', local_port))
    except Exception as e:
        print(f"Failed to bind: {e}")
        return

    print(f"Bound to {local_port}. Sending Invite to {TARGET_PORT}...")
    
    token_val = 0x12345678
    ssrc = 0x11223344
    name = "Auracle"
    sig=b"\xff\xff"; cmd=b"IN"; ver=struct.pack("!I",2); token=struct.pack("!I",token_val); ssrc_bytes=struct.pack("!I",ssrc)
    pkt=sig+cmd+ver+token+ssrc_bytes+name.encode()+b"\x00"
    
    sock.sendto(pkt, (IP, TARGET_PORT))
    
    sock.settimeout(2)
    try:
        data, addr = sock.recvfrom(1024)
        print(f"Received: {data.hex()}")
        if data[0:2] == b"\xff\xff":
            print(f"Type: {data[2:4]}")
    except socket.timeout:
        print("Timeout")
        
    sock.close()

if __name__ == "__main__":
    try_connect(5004)
    try_connect(5003)
    try_connect(15005)
