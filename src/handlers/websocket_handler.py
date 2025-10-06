"""
WebSocket Handler for WebRTC Signaling
Handles WebSocket connections and message routing for WebRTC signaling
"""

import json
import logging
from typing import Dict, Set, List, Optional
from fastapi import WebSocket
from ..models.signal_data import SignalData

logger = logging.getLogger(__name__)

class WebSocketHandler:
    def __init__(self):
        # Store active WebSocket connections by room
        self.rooms: Dict[str, Set[WebSocket]] = {}
        # Store connection metadata
        self.connection_metadata: Dict[WebSocket, Dict] = {}
    
    @property
    def active_connections(self) -> Set[WebSocket]:
        """Get all active connections across all rooms"""
        all_connections = set()
        for room_connections in self.rooms.values():
            all_connections.update(room_connections)
        return all_connections
    
    async def connect(self, websocket: WebSocket, room_id: str, username: str = None):
        """Accept WebSocket connection and add to room"""
        # Add to room
        if room_id not in self.rooms:
            self.rooms[room_id] = set()
        
        self.rooms[room_id].add(websocket)
        
        # Store connection metadata
        self.connection_metadata[websocket] = {
            "room_id": room_id,
            "username": username,
            "connected_at": None  # Could add timestamp here
        }
        
        logger.info(f"User {username} connected to room {room_id}")
        
        # Notify other clients in the room about new connection
        await self.broadcast_to_room(room_id, {
            "type": "user_joined",
            "room_id": room_id,
            "username": username,
            "connected_users": len(self.rooms[room_id])
        }, exclude_websocket=websocket)
    
    async def disconnect(self, websocket: WebSocket, room_id: str):
        """Remove WebSocket connection from room"""
        if room_id in self.rooms:
            self.rooms[room_id].discard(websocket)
            
            # Clean up empty rooms
            if not self.rooms[room_id]:
                del self.rooms[room_id]
        
        # Remove metadata
        if websocket in self.connection_metadata:
            del self.connection_metadata[websocket]
        
        logger.info(f"Client disconnected from room {room_id}")
        
        # Notify other clients in the room about disconnection
        if room_id in self.rooms:
            await self.broadcast_to_room(room_id, {
                "type": "user_left",
                "room_id": room_id,
                "connected_users": len(self.rooms[room_id])
            })
    
    async def handle_message(self, room_id: str, websocket: WebSocket, message: Dict):
        """Handle incoming WebRTC signaling messages"""
        message_type = message.get("type")
        
        try:
            if message_type == "offer":
                await self.handle_offer(room_id, websocket, message)
            elif message_type == "answer":
                await self.handle_answer(room_id, websocket, message)
            elif message_type == "ice_candidate":
                await self.handle_ice_candidate(room_id, websocket, message)
            elif message_type == "ping":
                await self.handle_ping(websocket)
            else:
                logger.warning(f"Unknown message type: {message_type}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": f"Unknown message type: {message_type}"
                }))
        
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "Internal server error"
            }))
    
    async def handle_offer(self, room_id: str, sender: WebSocket, message: Dict):
        """Handle WebRTC offer message"""
        # Forward offer to all other clients in the room
        await self.broadcast_to_room(room_id, {
            "type": "offer",
            "offer": message.get("offer"),
            "from": "signaling_server"
        }, exclude_websocket=sender)
        
        logger.info(f"Offer forwarded in room {room_id}")
    
    async def handle_answer(self, room_id: str, sender: WebSocket, message: Dict):
        """Handle WebRTC answer message"""
        # Forward answer to all other clients in the room
        await self.broadcast_to_room(room_id, {
            "type": "answer",
            "answer": message.get("answer"),
            "from": "signaling_server"
        }, exclude_websocket=sender)
        
        logger.info(f"Answer forwarded in room {room_id}")
    
    async def handle_ice_candidate(self, room_id: str, sender: WebSocket, message: Dict):
        """Handle ICE candidate message"""
        # Forward ICE candidate to all other clients in the room
        await self.broadcast_to_room(room_id, {
            "type": "ice_candidate",
            "candidate": message.get("candidate"),
            "from": "signaling_server"
        }, exclude_websocket=sender)
        
        logger.info(f"ICE candidate forwarded in room {room_id}")
    
    async def handle_ping(self, websocket: WebSocket):
        """Handle ping message"""
        await websocket.send_text(json.dumps({
            "type": "pong"
        }))
    
    async def broadcast_to_room(self, room_id: str, message: Dict, exclude_websocket: Optional[WebSocket] = None):
        """Broadcast message to all clients in a room"""
        if room_id not in self.rooms:
            return
        
        message_json = json.dumps(message)
        disconnected_clients = set()
        
        for websocket in self.rooms[room_id]:
            if websocket != exclude_websocket:
                try:
                    await websocket.send_text(message_json)
                except Exception as e:
                    logger.error(f"Error sending message to client: {e}")
                    disconnected_clients.add(websocket)
        
        # Clean up disconnected clients
        for websocket in disconnected_clients:
            await self.disconnect(websocket, room_id)
    
    def get_room_info(self, room_id: str) -> Optional[Dict]:
        """Get information about a specific room"""
        if room_id not in self.rooms:
            return None
        
        return {
            "room_id": room_id,
            "connected_users": len(self.rooms[room_id]),
            "is_active": True
        }
    
    def list_rooms(self) -> List[Dict]:
        """List all active rooms"""
        return [
            {
                "room_id": room_id,
                "connected_users": len(connections),
                "is_active": True
            }
            for room_id, connections in self.rooms.items()
        ]
