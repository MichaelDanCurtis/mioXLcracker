## Capturing AppleMIDI / RTP-MIDI handshake from Auracle X

This folder contains helper scripts to capture the exact bytes the Auracle X app sends when it performs an AppleMIDI handshake (RTP-MIDI invites) and the device replies with `OK` or `NO`.

There are two primary approaches:

1) tcpdump capture + scapy extraction

- Run tcpdump (requires sudo) on the machine while reproducing the scenario in Auracle X (attempt to open remote control/preset/query). Example:

  sudo ./capture_rtpmidi_tcpdump.sh en0 rtpmidi_capture.pcap

- Trigger the behavior in Auracle X that attempts the handshake and/or connect to the device.
- Stop tcpdump once the handshake is complete (Ctrl-C).
- Extract UDP payloads from the pcap with scapy:

  python3 extract_rtpmidi_packets.py rtpmidi_capture.pcap > extracted.txt

- Inspect `extracted.txt` for payloads sent from your Mac to the device on port 5003 (control) & 5006 (RTP-MIDI). Copy the hex payload and replay it:

  python3 replay_hex_udp.py <device-ip> 5003 <hexpayload>

2) Live hooking with Frida (more robust, prints exact buffer when 'sendto' is called)

- Install frida-tools:
  pip3 install frida-tools

- Run Auracle X and find its process id (PID) and start Frida to attach & run the hook script:

  frida -p <PID> -l frida_sendto_hook.js

- When Auracle X sends a packet, Frida will print hex payloads for destination ports 5003 and 5006.

- Replay the captured hex with `replay_hex_udp.py`.
  - Or use the Adobe INVITE builder and replay tool to construct and send a custom INVITE:
    python3 tools/packet_capture/applemidi_invite_replay.py <device-ip> 5003 --build --ssrc 0x11223344 --token 0xaabbccdd --name 'pyClient' --port-field 5006 --local-port 5004

Notes and limitations:
- Modern macOS may block DTrace or frida instrumentation under System Integrity Protection (SIP). You may need to disable SIP or use a machine where you can run frida.
- `tcpdump` is the simplest approach and does not require modifying the app.
- Use Wireshark or tshark if you prefer a GUI. pcap output can also be inspected in Wireshark, where you can right-click and export packet data as hex.

Next steps once you have a working capture and replay:
- Use the captured payloads to infer any challenge/response tokens or session IDs.
- Report back with the hex payloads (especially those sent to port 5003) and we will analyze them to identify the exact handshake sequence and reconstruct a minimal client to query preset names without Auracle X.

