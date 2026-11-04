import socket, sys, time

IP = "192.168.1.199"
PORTS = range(5000, 5020)

def encode7(val, size=2):
    bd = bytearray()
    while val > 0:
        bd.insert(0, val & 0x7f)
        val >>= 7
    while len(bd) < size:
        bd.insert(0, 0x00)
    return bd

def chksum(data):
    cs = 128 - (sum(data) % 128)
    return 0 if cs == 128 else cs

def sysex_preset_name(preset, txn):
    mfid = b"\x00\x01\x73"; msgcls = b"\x7d"; devid = b"\x00"*7; foo = b"\x00"*12
    cmd_prefix = bytes([0x03, 0x03, 0x02, 0x05, 0x04, 0x01])
    cmd_mid = bytes([0x09]) 
    preset_byte = bytes([preset])
    cmd_suffix = bytes([0x04, 0x01, 0x01, 0x02])
    cmd_data = cmd_prefix + cmd_mid + preset_byte + cmd_suffix
    clen = bytes([len(cmd_data)])
    txn_bytes = encode7(txn, 2)
    body = foo + txn_bytes + clen + cmd_data
    syx = b"\xF0" + mfid + msgcls + devid + body + bytes([chksum(body)]) + b"\xF7"
    return syx

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(0.2)

# Construct a query for Preset 1
query = sysex_preset_name(1, 123)

# Wrap in RTP-MIDI (SSRC=0x12345678)
# V=2, P=0, X=0, CC=0, M=0, PT=0x61 (97)
rtp_header = b'\x80\x61\x00\x01\x00\x00\x00\x00\x12\x34\x56\x78'
packet = rtp_header + b'\x00' + query

print(f"Spraying query to {IP} ports 5000-5019...", flush=True)

for port in PORTS:
    sock.sendto(packet, (IP, port))
    try:
        data, addr = sock.recvfrom(1024)
        print(f"Response from {port}: {data.hex()}", flush=True)
    except socket.timeout:
        pass

sock.close()
print("Done.", flush=True)
