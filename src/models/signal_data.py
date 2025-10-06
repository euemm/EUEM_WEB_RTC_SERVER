"""
Signal Data Models
Pydantic models for WebRTC signaling data validation
"""

from typing import Optional, Any, Dict
from pydantic import BaseModel, Field

class SignalData(BaseModel):
    """Base model for WebRTC signaling data"""
    type: str = Field(..., description="Type of signaling message")
    room_id: Optional[str] = Field(None, description="Room identifier")
    timestamp: Optional[float] = Field(None, description="Message timestamp")

class OfferSignal(SignalData):
    """Model for WebRTC offer signaling"""
    type: str = Field("offer", description="Message type")
    offer: Dict[str, Any] = Field(..., description="WebRTC offer object")

class AnswerSignal(SignalData):
    """Model for WebRTC answer signaling"""
    type: str = Field("answer", description="Message type")
    answer: Dict[str, Any] = Field(..., description="WebRTC answer object")

class IceCandidateSignal(SignalData):
    """Model for ICE candidate signaling"""
    type: str = Field("ice_candidate", description="Message type")
    candidate: Dict[str, Any] = Field(..., description="ICE candidate object")

class RoomInfo(BaseModel):
    """Model for room information"""
    room_id: str = Field(..., description="Room identifier")
    connected_users: int = Field(..., description="Number of connected users")
    is_active: bool = Field(True, description="Whether room is active")

class ConnectionInfo(BaseModel):
    """Model for connection information"""
    room_id: str = Field(..., description="Room identifier")
    connected_at: Optional[float] = Field(None, description="Connection timestamp")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional connection metadata")
