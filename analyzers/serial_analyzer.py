"""
Serial Protocol Analyzer
Analyzes serial communication (RS-232, RS-485, UART, etc.)
"""

import serial
import logging
from typing import Dict, List, Optional
import time

logger = logging.getLogger(__name__)


class SerialAnalyzer:
    """Analyzer for serial communication protocols."""
    
    def __init__(self, port: str, baudrate: int = 9600, 
                 bytesize: int = 8, parity: str = 'N', 
                 stopbits: int = 1, timeout: float = 1.0):
        """
        Initialize serial analyzer.
        
        Args:
            port: Serial port (e.g., '/dev/ttyUSB0', 'COM1')
            baudrate: Communication speed
            bytesize: Number of data bits
            parity: Parity checking ('N', 'E', 'O', 'M', 'S')
            stopbits: Number of stop bits
            timeout: Read timeout in seconds
        """
        self.port = port
        self.baudrate = baudrate
        self.bytesize = bytesize
        self.parity = parity
        self.stopbits = stopbits
        self.timeout = timeout
        self.connection: Optional[serial.Serial] = None
        
    def connect(self) -> bool:
        """
        Open serial connection.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.connection = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=self.bytesize,
                parity=self.parity,
                stopbits=self.stopbits,
                timeout=self.timeout
            )
            logger.info(f"Connected to {self.port} @ {self.baudrate} baud")
            return True
        except serial.SerialException as e:
            logger.error(f"Failed to connect to {self.port}: {e}")
            return False
    
    def disconnect(self):
        """Close serial connection."""
        if self.connection and self.connection.is_open:
            self.connection.close()
            logger.info(f"Disconnected from {self.port}")
    
    def read_bytes(self, num_bytes: int = 1) -> bytes:
        """
        Read bytes from serial port.
        
        Args:
            num_bytes: Number of bytes to read
            
        Returns:
            Bytes read from port
        """
        if not self.connection or not self.connection.is_open:
            logger.warning("Serial port not open")
            return b''
        
        try:
            data = self.connection.read(num_bytes)
            if data:
                logger.debug(f"Read {len(data)} bytes: {data.hex()}")
            return data
        except serial.SerialException as e:
            logger.error(f"Error reading from serial port: {e}")
            return b''
    
    def write_bytes(self, data: bytes) -> int:
        """
        Write bytes to serial port.
        
        Args:
            data: Bytes to write
            
        Returns:
            Number of bytes written
        """
        if not self.connection or not self.connection.is_open:
            logger.warning("Serial port not open")
            return 0
        
        try:
            written = self.connection.write(data)
            logger.debug(f"Wrote {written} bytes: {data.hex()}")
            return written
        except serial.SerialException as e:
            logger.error(f"Error writing to serial port: {e}")
            return 0
    
    def capture(self, duration: float = 10.0) -> List[Dict]:
        """
        Capture serial traffic.
        
        Args:
            duration: Capture duration in seconds
            
        Returns:
            List of captured frames with timestamp and data
        """
        if not self.connection or not self.connection.is_open:
            logger.error("Serial port not open")
            return []
        
        logger.info(f"Capturing serial traffic for {duration} seconds...")
        frames = []
        start_time = time.time()
        
        while time.time() - start_time < duration:
            if self.connection.in_waiting > 0:
                data = self.connection.read(self.connection.in_waiting)
                frames.append({
                    'timestamp': time.time(),
                    'data': data,
                    'hex': data.hex(),
                    'length': len(data)
                })
        
        logger.info(f"Captured {len(frames)} frames")
        return frames
    
    def get_info(self) -> Dict:
        """
        Get serial port configuration.
        
        Returns:
            Dictionary with port settings
        """
        return {
            'port': self.port,
            'baudrate': self.baudrate,
            'bytesize': self.bytesize,
            'parity': self.parity,
            'stopbits': self.stopbits,
            'timeout': self.timeout,
            'connected': self.connection.is_open if self.connection else False
        }
