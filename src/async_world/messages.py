#!/usr/bin/env python3
"""
Message System for Async World Generation

Defines message types for communication between the main thread (rendering)
and the world generation worker thread via thread-safe queues.
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional
from enum import Enum


class MessageType(Enum):
    """Types of messages that can be sent between threads."""
    CHUNK_REQUEST = "chunk_request"
    CHUNK_RESPONSE = "chunk_response"
    CHUNK_CANCEL = "chunk_cancel"
    STATUS_UPDATE = "status_update"
    SHUTDOWN = "shutdown"


class Priority(Enum):
    """Priority levels for chunk generation requests."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


@dataclass
class ChunkRequest:
    """Request to generate a specific chunk."""
    chunk_x: int
    chunk_y: int
    priority: Priority = Priority.NORMAL
    request_id: Optional[str] = None
    
    def __post_init__(self):
        if self.request_id is None:
            self.request_id = f"chunk_{self.chunk_x}_{self.chunk_y}"


@dataclass
class ChunkResponse:
    """Response containing generated chunk data."""
    chunk_x: int
    chunk_y: int
    chunk_data: Dict[str, Any]
    request_id: str
    generation_time: float
    success: bool = True
    error_message: Optional[str] = None


@dataclass
class ChunkCancel:
    """Request to cancel chunk generation."""
    chunk_x: int
    chunk_y: int
    request_id: str


@dataclass
class StatusUpdate:
    """Status update from worker thread."""
    message: str
    worker_id: str
    chunks_in_queue: int
    chunks_generated: int
    cache_size: int


@dataclass
class ShutdownMessage:
    """Signal to shutdown worker thread."""
    reason: str = "Normal shutdown"


@dataclass
class Message:
    """Wrapper for all message types with metadata."""
    message_type: MessageType
    payload: Any
    timestamp: float
    sender: str

    def __lt__(self, other):
        """Enable comparison for priority queue."""
        if not isinstance(other, Message):
            return NotImplemented
        return self.timestamp < other.timestamp

    def __eq__(self, other):
        """Enable equality comparison."""
        if not isinstance(other, Message):
            return NotImplemented
        return (self.message_type == other.message_type and
                self.timestamp == other.timestamp and
                self.sender == other.sender)

    def __hash__(self):
        """Enable hashing for use in sets."""
        return hash((self.message_type, self.timestamp, self.sender))
    
    @classmethod
    def chunk_request(cls, chunk_x: int, chunk_y: int, priority: Priority = Priority.NORMAL, 
                     sender: str = "main") -> 'Message':
        """Create a chunk request message."""
        import time
        return cls(
            message_type=MessageType.CHUNK_REQUEST,
            payload=ChunkRequest(chunk_x, chunk_y, priority),
            timestamp=time.time(),
            sender=sender
        )
    
    @classmethod
    def chunk_response(cls, chunk_x: int, chunk_y: int, chunk_data: Dict[str, Any],
                      request_id: str, generation_time: float, success: bool = True,
                      error_message: Optional[str] = None, sender: str = "worker") -> 'Message':
        """Create a chunk response message."""
        import time
        return cls(
            message_type=MessageType.CHUNK_RESPONSE,
            payload=ChunkResponse(chunk_x, chunk_y, chunk_data, request_id, 
                                generation_time, success, error_message),
            timestamp=time.time(),
            sender=sender
        )
    
    @classmethod
    def chunk_cancel(cls, chunk_x: int, chunk_y: int, request_id: str, 
                    sender: str = "main") -> 'Message':
        """Create a chunk cancel message."""
        import time
        return cls(
            message_type=MessageType.CHUNK_CANCEL,
            payload=ChunkCancel(chunk_x, chunk_y, request_id),
            timestamp=time.time(),
            sender=sender
        )
    
    @classmethod
    def status_update(cls, message: str, worker_id: str, chunks_in_queue: int,
                     chunks_generated: int, cache_size: int, sender: str = "worker") -> 'Message':
        """Create a status update message."""
        import time
        return cls(
            message_type=MessageType.STATUS_UPDATE,
            payload=StatusUpdate(message, worker_id, chunks_in_queue, chunks_generated, cache_size),
            timestamp=time.time(),
            sender=sender
        )
    
    @classmethod
    def shutdown(cls, reason: str = "Normal shutdown", sender: str = "main") -> 'Message':
        """Create a shutdown message."""
        import time
        return cls(
            message_type=MessageType.SHUTDOWN,
            payload=ShutdownMessage(reason),
            timestamp=time.time(),
            sender=sender
        )


class MessageBus:
    """
    Thread-safe message bus for communication between main and worker threads.
    
    Uses Python's queue.Queue for thread-safe message passing.
    """
    
    def __init__(self, max_queue_size: int = 1000):
        """
        Initialize the message bus.
        
        Args:
            max_queue_size: Maximum number of messages in each queue
        """
        import queue
        
        # Queue for messages from main thread to worker thread
        self.to_worker = queue.PriorityQueue(maxsize=max_queue_size)
        
        # Queue for messages from worker thread to main thread
        self.to_main = queue.Queue(maxsize=max_queue_size)
        
        # Statistics
        self.messages_sent = 0
        self.messages_received = 0
    
    def send_to_worker(self, message: Message, block: bool = True, timeout: Optional[float] = None):
        """
        Send a message to the worker thread.
        
        Args:
            message: Message to send
            block: Whether to block if queue is full
            timeout: Timeout for blocking operations
        """
        try:
            # Use priority based on message type and payload priority
            priority = self._get_message_priority(message)
            self.to_worker.put((priority, message), block=block, timeout=timeout)
            self.messages_sent += 1
        except Exception as e:
            print(f"Failed to send message to worker: {e}")
    
    def send_to_main(self, message: Message, block: bool = True, timeout: Optional[float] = None):
        """
        Send a message to the main thread.

        Args:
            message: Message to send
            block: Whether to block if queue is full
            timeout: Timeout for blocking operations
        """
        try:
            self.to_main.put(message, block=block, timeout=timeout)
            self.messages_sent += 1
        except Exception as e:
            print(f"Failed to send message to main: {e}")
    
    def receive_from_worker(self, block: bool = False, timeout: Optional[float] = None) -> Optional[Message]:
        """
        Receive a message from the worker thread.

        Args:
            block: Whether to block waiting for message
            timeout: Timeout for blocking operations

        Returns:
            Message if available, None otherwise
        """
        import queue
        try:
            message = self.to_main.get(block=block, timeout=timeout)
            self.messages_received += 1
            return message
        except queue.Empty:
            return None
        except Exception as e:
            print(f"Failed to receive message from worker: {e}")
            return None
    
    def receive_from_main(self, block: bool = True, timeout: Optional[float] = None) -> Optional[Message]:
        """
        Receive a message from the main thread.

        Args:
            block: Whether to block waiting for message
            timeout: Timeout for blocking operations

        Returns:
            Message if available, None otherwise
        """
        import queue
        try:
            _priority, message = self.to_worker.get(block=block, timeout=timeout)
            self.messages_received += 1
            return message
        except queue.Empty:
            return None
        except Exception as e:
            print(f"Failed to receive message from main: {e}")
            return None
    
    def _get_message_priority(self, message: Message) -> int:
        """Get numeric priority for message (lower number = higher priority)."""
        if message.message_type == MessageType.SHUTDOWN:
            return 0  # Highest priority
        elif message.message_type == MessageType.CHUNK_CANCEL:
            return 1  # High priority
        elif message.message_type == MessageType.CHUNK_REQUEST:
            # Use request priority
            if hasattr(message.payload, 'priority'):
                priority_map = {
                    Priority.URGENT: 2,
                    Priority.HIGH: 3,
                    Priority.NORMAL: 4,
                    Priority.LOW: 5
                }
                return priority_map.get(message.payload.priority, 4)
            return 4  # Normal priority
        else:
            return 6  # Low priority
    
    def get_stats(self) -> Dict[str, int]:
        """Get message bus statistics."""
        return {
            'messages_sent': self.messages_sent,
            'messages_received': self.messages_received,
            'to_worker_size': self.to_worker.qsize(),
            'to_main_size': self.to_main.qsize()
        }
