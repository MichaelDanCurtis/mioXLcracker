#!/bin/zsh
# Capture RTP-MIDI and related control packets for analysis
# Usage: sudo ./capture_rtpmidi_tcpdump.sh <interface> <output.pcap>
# Example: sudo ./capture_rtpmidi_tcpdump.sh en0 rtpmidi_capture.pcap

set -euo pipefail

if [ "$#" -lt 2 ]; then
  echo "Usage: sudo $0 <interface> <output.pcap>"
  exit 1
fi

IFACE="$1"
OUT="$2"

# Capture only UDP packets on ports 5003/5004/5005/5006 which are used by RTP-MIDI implementations
# Use snaplen of 0 to capture full packets
sudo tcpdump -i "$IFACE" -s 0 -w "$OUT" "udp and (port 5003 or port 5004 or port 5005 or port 5006)"
