"""
Modbus Protocol Analyzer
Analyzes Modbus RTU, TCP, and ASCII communications
"""

import asyncio
import logging
from typing import Dict, List, Optional
from pymodbus.client import AsyncModbusTcpClient, AsyncModbusSerialClient
from pymodbus import FramerType

logger = logging.getLogger(__name__)


class ModbusAnalyzer:
    """Analyzer for Modbus protocol variants."""
    
    def __init__(self, mode: str = "tcp", **kwargs):
        """
        Initialize Modbus analyzer.
        
        Args:
            mode: Protocol mode ('tcp', 'rtu', 'ascii')
            **kwargs: Connection parameters specific to mode
                For TCP: host, port
                For RTU/ASCII: port, baudrate, bytesize, parity, stopbits
        """
        self.mode = mode.lower()
        self.kwargs = kwargs
        self.client: Optional[AsyncModbusTcpClient | AsyncModbusSerialClient] = None
        
    async def connect(self) -> bool:
        """
        Connect to Modbus device.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.mode == "tcp":
                host = self.kwargs.get('host', 'localhost')
                port = self.kwargs.get('port', 502)
                self.client = AsyncModbusTcpClient(
                    host=host,
                    port=port,
                    framer=FramerType.SOCKET
                )
                logger.info(f"Connecting to Modbus TCP at {host}:{port}")
                
            elif self.mode in ["rtu", "ascii"]:
                port = self.kwargs.get('port', '/dev/ttyUSB0')
                baudrate = self.kwargs.get('baudrate', 9600)
                framer = FramerType.RTU if self.mode == "rtu" else FramerType.ASCII
                
                self.client = AsyncModbusSerialClient(
                    port=port,
                    baudrate=baudrate,
                    bytesize=self.kwargs.get('bytesize', 8),
                    parity=self.kwargs.get('parity', 'N'),
                    stopbits=self.kwargs.get('stopbits', 1),
                    framer=framer
                )
                logger.info(f"Connecting to Modbus {self.mode.upper()} on {port} @ {baudrate} baud")
            
            else:
                logger.error(f"Unsupported Modbus mode: {self.mode}")
                return False
            
            await self.client.connect()
            return self.client.connected
            
        except Exception as e:
            logger.error(f"Failed to connect to Modbus device: {e}")
            return False
    
    async def disconnect(self):
        """Close Modbus connection."""
        if self.client:
            self.client.close()
            logger.info("Disconnected from Modbus device")
    
    async def read_coils(self, address: int, count: int, device_id: int = 1) -> Optional[List[bool]]:
        """
        Read coils (function code 0x01).
        
        Args:
            address: Starting address
            count: Number of coils to read
            device_id: Modbus device/slave ID
            
        Returns:
            List of coil values or None on error
        """
        if not self.client or not self.client.connected:
            logger.error("Not connected to Modbus device")
            return None
        
        try:
            result = await self.client.read_coils(address, count, device_id=device_id)
            if result.isError():
                logger.error(f"Error reading coils: {result}")
                return None
            return result.bits[:count]
        except Exception as e:
            logger.error(f"Exception reading coils: {e}")
            return None
    
    async def read_holding_registers(self, address: int, count: int, device_id: int = 1) -> Optional[List[int]]:
        """
        Read holding registers (function code 0x03).
        
        Args:
            address: Starting address
            count: Number of registers to read
            device_id: Modbus device/slave ID
            
        Returns:
            List of register values or None on error
        """
        if not self.client or not self.client.connected:
            logger.error("Not connected to Modbus device")
            return None
        
        try:
            result = await self.client.read_holding_registers(address, count, device_id=device_id)
            if result.isError():
                logger.error(f"Error reading holding registers: {result}")
                return None
            return result.registers
        except Exception as e:
            logger.error(f"Exception reading holding registers: {e}")
            return None
    
    async def write_register(self, address: int, value: int, device_id: int = 1) -> bool:
        """
        Write single register (function code 0x06).
        
        Args:
            address: Register address
            value: Value to write
            device_id: Modbus device/slave ID
            
        Returns:
            True if successful, False otherwise
        """
        if not self.client or not self.client.connected:
            logger.error("Not connected to Modbus device")
            return False
        
        try:
            result = await self.client.write_register(address, value, device_id=device_id)
            return not result.isError()
        except Exception as e:
            logger.error(f"Exception writing register: {e}")
            return False
    
    async def scan_devices(self, start_id: int = 1, end_id: int = 247, 
                           concurrency: int = 10, timeout: float = 0.5) -> List[int]:
        """
        Scan for responding Modbus devices using concurrent requests.
        
        Args:
            start_id: Starting device ID
            end_id: Ending device ID
            concurrency: Maximum concurrent scan requests
            timeout: Timeout per device probe in seconds
            
        Returns:
            List of responding device IDs
        """
        if not self.client or not self.client.connected:
            logger.error("Not connected to Modbus")
            return []
        
        logger.info(f"Scanning for Modbus devices {start_id}-{end_id} (concurrency={concurrency})...")
        responding_devices = []
        
        async def probe_device(device_id: int) -> Optional[int]:
            """Probe a single device and return its ID if it responds."""
            try:
                result = await asyncio.wait_for(
                    self.client.read_holding_registers(0, 1, device_id=device_id),
                    timeout=timeout
                )
                if not result.isError():
                    logger.info(f"Found device at ID {device_id}")
                    return device_id
            except asyncio.TimeoutError:
                pass  # Device didn't respond in time
            except Exception:
                pass  # Device didn't respond
            return None
        
        # Use semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(concurrency)
        
        async def limited_probe(device_id: int) -> Optional[int]:
            async with semaphore:
                return await probe_device(device_id)
        
        # Create all probe tasks
        tasks = [limited_probe(device_id) for device_id in range(start_id, end_id + 1)]
        
        # Execute all probes concurrently with limited parallelism
        results = await asyncio.gather(*tasks)
        
        # Filter out None results (non-responding devices)
        responding_devices = [device_id for device_id in results if device_id is not None]
        responding_devices.sort()  # Return in ascending order
        
        logger.info(f"Scan complete. Found {len(responding_devices)} devices.")
        return responding_devices
    
    def get_info(self) -> Dict:
        """
        Get Modbus connection information.
        
        Returns:
            Dictionary with connection settings
        """
        return {
            'mode': self.mode,
            'connected': self.client.connected if self.client else False,
            **self.kwargs
        }
