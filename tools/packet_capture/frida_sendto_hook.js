// Hook libc `sendto` to capture UDP data payloads and print hex for RTP-MIDI ports
// Usage: frida -p <pid> -l frida_sendto_hook.js

function toHex(buffer) {
    return Array.prototype.map.call(buffer, function (x) {
        return ('0' + (x & 0xFF).toString(16)).slice(-2);
    }).join('');
}

var sendto = Module.findExportByName(null, 'sendto');
if (!sendto) {
    console.error('sendto not found');
} else {
    Interceptor.attach(sendto, {
        onEnter: function (args) {
            try {
                var buf = args[1];
                var len = parseInt(args[2]);
                var sockaddr = args[4];
                var family = Memory.readU16(sockaddr);
                if (family == 2) { // AF_INET
                    var port = Memory.readU16(sockaddr.add(2));
                    // port is in network byte order
                    var portVal = ((port & 0xff) << 8) | ((port & 0xff00) >> 8);
                    if (portVal == 5003 || portVal == 5006) {
                        var bytes = Memory.readByteArray(buf, len);
                        var arr = new Uint8Array(bytes);
                        var hexStr = toHex(arr);
                        console.log('sendto port=' + portVal + ' len=' + len);
                        console.log(hexStr);
                        // detect AppleMIDI ctrl INVITE/OK/NO ('FF FF IN/OK/NO')
                        if (len >= 4 && arr[0] == 0xFF && arr[1] == 0xFF) {
                            var cmd = String.fromCharCode(arr[2], arr[3]);
                            if (cmd == 'IN') console.log('-- AppleMIDI INVITE (IN) --');
                            else if (cmd == 'OK') console.log('-- AppleMIDI OK --');
                            else if (cmd == 'NO') console.log('-- AppleMIDI NO --');
                        }
                    }
                }
            } catch (e) {
                console.error('frida hook error: ' + e);
            }
        },
        onLeave: function (retval) {}
    });
}
