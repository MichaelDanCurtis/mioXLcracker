"""
Network Protocol Analyzer
Analyzes network-based hardware communication protocols
"""

import logging
from typing import Dict, List, Optional
from scapy.all import sniff, wrpcap, IP, TCP, UDP

logger = logging.getLogger(__name__)


class NetworkAnalyzer:
    """Analyzer for network-based protocols."""
    
    def __init__(self, interface: Optional[str] = None, 
                 filter_str: Optional[str] = None):
        """
        Initialize network analyzer.
        
        Args:
            interface: Network interface to monitor (None for default)
            filter_str: BPF filter string (e.g., 'tcp port 502')
        """
        self.interface = interface
        self.filter_str = filter_str
        self.packets: List = []
        
    def capture(self, count: int = 100, timeout: Optional[int] = None) -> List:
        """
        Capture network packets.
        
        Args:
            count: Number of packets to capture (0 for unlimited)
            timeout: Capture timeout in seconds
            
        Returns:
            List of captured packets
        """
        logger.info(f"Capturing packets on interface {self.interface or 'default'}")
        if self.filter_str:
            logger.info(f"Using filter: {self.filter_str}")
        
        try:
            self.packets = sniff(
                iface=self.interface,
                filter=self.filter_str,
                count=count,
                timeout=timeout
            )
            logger.info(f"Captured {len(self.packets)} packets")
            return self.packets
        except Exception as e:
            logger.error(f"Error capturing packets: {e}")
            return []
    
    def save_capture(self, filename: str):
        """
        Save captured packets to file.
        
        Args:
            filename: Output pcap filename
        """
        if not self.packets:
            logger.warning("No packets to save")
            return
        
        try:
            wrpcap(filename, self.packets)
            logger.info(f"Saved {len(self.packets)} packets to {filename}")
        except Exception as e:
            logger.error(f"Error saving capture: {e}")
    
    def analyze_packets(self) -> Dict:
        """
        Analyze captured packets.
        
        Returns:
            Dictionary with packet statistics
        """
        if not self.packets:
            logger.warning("No packets to analyze")
            return {}
        
        stats = {
            'total_packets': len(self.packets),
            'protocols': {},
            'endpoints': set(),
            'ports': set()
        }
        
        for pkt in self.packets:
            # Protocol distribution
            if IP in pkt:
                proto = 'IP'
                if TCP in pkt:
                    proto = 'TCP'
                    stats['ports'].add(pkt[TCP].sport)
                    stats['ports'].add(pkt[TCP].dport)
                elif UDP in pkt:
                    proto = 'UDP'
                    stats['ports'].add(pkt[UDP].sport)
                    stats['ports'].add(pkt[UDP].dport)
                
                stats['protocols'][proto] = stats['protocols'].get(proto, 0) + 1
                stats['endpoints'].add(pkt[IP].src)
                stats['endpoints'].add(pkt[IP].dst)
        
        stats['endpoints'] = list(stats['endpoints'])
        stats['ports'] = sorted(list(stats['ports']))
        
        return stats
    
    def filter_modbus_tcp(self) -> List:
        """
        Filter for Modbus TCP packets (port 502).
        
        Returns:
            List of Modbus TCP packets
        """
        modbus_packets = []
        for pkt in self.packets:
            if TCP in pkt and (pkt[TCP].sport == 502 or pkt[TCP].dport == 502):
                modbus_packets.append(pkt)
        
        logger.info(f"Found {len(modbus_packets)} Modbus TCP packets")
        return modbus_packets
    
    def get_info(self) -> Dict:
        """
        Get network analyzer information.
        
        Returns:
            Dictionary with analyzer settings
        """
        return {
            'interface': self.interface,
            'filter': self.filter_str,
            'packets_captured': len(self.packets)
        }
