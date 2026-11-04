#!/usr/bin/env python3
"""
Probe various SysEx message combinations to port 5006 to see if any yield a response.
Try changing message class and device id fields.
"""
import socket, sys, struct, time

IP = sys.argv[1] if len(sys.argv)>1 else '192.168.1.199'
PORT = 5006

# Construct a nominal 'get number of presets' message body
mfid = b"\x00\x01\x73"
base_cmds = {
    'num_presets': bytes([0x03,0x02,0x01]),
    'current_preset': bytes([0x03,0x03,0x01])
}

# We'll build a general sysex builder

def encode7(val, size=2):
    bd = bytearray()
    while val > 0:
        bd.insert(0, val & 0x7f)
        val >>= 7
    while len(bd) < size:
        bd.insert(0, 0)
    return bytes(bd)


def chksum(data):
    cs = 128 - (sum(data) % 128)
    return 0 if cs == 128 else cs


def build_sysex(msgcls=0x7d, devid=bytes([0]*7), body=b''):
    syx = b"\xF0" + mfid + bytes([msgcls]) + devid + body + bytes([chksum(devid+body)]) + b"\xF7"
    return syx


def build_body_for_num(txn=1):
    foo = b"\x00"*12
    flags=0x03; cmd=0x02; nargs=0x01; arg1 = bytes([0x01,0x01,0x14])
    cmd_data = bytes([flags,cmd,nargs]) + arg1
    clen = encode7(len(cmd_data), 2)
    body = foo + encode7(txn,2) + clen + cmd_data
    return body


def send_and_recv(s, data):
    s.sendto(data, (IP, PORT))
    # listen for a short time
    s.settimeout(0.35)
    try:
        resp, addr = s.recvfrom(4096)
        return resp
    except socket.timeout:
        return None


def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(('',0))
    print('bound to', s.getsockname())

    bodies = [build_body_for_num(1)]
    msgcls_options = [0x7d, 0x00, 0x0E, 0x7E, 0x7F]
    devid_options = [bytes([0]*7), bytes([1]*7), bytes([0x7f]*7), bytes([0x00, 0x00, 0x00, 1, 0,0,0])]

    for b_idx, body in enumerate(bodies):
        for msgcls in msgcls_options:
            for devid in devid_options:
                syx = build_sysex(msgcls, devid, body)
                print(f"Trying msgcls={hex(msgcls)} devid={devid.hex()} len={len(syx)}")
                resp = send_and_recv(s, syx)
                if resp:
                    print('RESPONSE LENGTH', len(resp), resp.hex())
                    return
                time.sleep(0.1)
    print('No responses found')

if __name__ == '__main__':
    main()
