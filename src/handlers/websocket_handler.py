"""
WebSocket Handler for WebRTC Signaling
Handles WebSocket connections and message routing for WebRTC signaling
"""

import json
import logging
import uuid
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
    
    async def connect(self, websocket: WebSocket, room_id: str, username: str = None, client_id: str = None):
        """Accept WebSocket connection and add to room"""
        # Generate client_id if not provided
        if not client_id:
            client_id = str(uuid.uuid4())
        
        # Add to room
        if room_id not in self.rooms:
            self.rooms[room_id] = set()
        
        self.rooms[room_id].add(websocket)
        
        # Store connection metadata including client_id
        self.connection_metadata[websocket] = {
            "room_id": room_id,
            "username": username,
            "client_id": client_id,
            "connected_at": None  # Could add timestamp here
        }
        
        logger.info(f"User {username} (client_id: {client_id}) connected to room {room_id}")
        
        # Get list of existing users in room (excluding this connection)
        existing_users = []
        for ws in self.rooms[room_id]:
            if ws != websocket and ws in self.connection_metadata:
                metadata = self.connection_metadata[ws]
                existing_users.append({
                    "client_id": metadata.get("client_id"),
                    "username": metadata.get("username")
                })
        
        # Send existing users list to the new user
        if existing_users:
            await websocket.send_text(json.dumps({
                "type": "users_in_room",
                "users": existing_users
            }))
        
        # Notify other clients in the room about new connection
        await self.broadcast_to_room(room_id, {
            "type": "user_joined",
            "room_id": room_id,
            "username": username,
            "client_id": client_id,
            "connected_users": len(self.rooms[room_id])
        }, exclude_websocket=websocket)
    
    async def disconnect(self, websocket: WebSocket, room_id: str):
        """Remove WebSocket connection from room"""
        # Get metadata before removing
        metadata = self.connection_metadata.get(websocket, {})
        client_id = metadata.get("client_id")
        username = metadata.get("username")
        
        logger.info(f"Client {client_id} ({username}) disconnecting from room {room_id}")
        
        if room_id in self.rooms:
            self.rooms[room_id].discard(websocket)
            
            # Clean up empty rooms
            if not self.rooms[room_id]:
                del self.rooms[room_id]
                logger.info(f"Room {room_id} is now empty, cleaned up")
        
        # Remove metadata
        if websocket in self.connection_metadata:
            del self.connection_metadata[websocket]
        
        # Notify other clients in the room about disconnection
        # THIS IS CRITICAL - Without this, other clients won't know user left!
        if room_id in self.rooms:
            remaining_users = len(self.rooms[room_id])
            await self.broadcast_to_room(room_id, {
                "type": "user_left",
                "room_id": room_id,
                "client_id": client_id,
                "username": username,
                "connected_users": remaining_users
            })
            logger.info(f"Notified {remaining_users} users about {username} ({client_id}) leaving room {room_id}")
        else:
            logger.info(f"No users remaining in room {room_id} to notify about {username} leaving")
    
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
        sender_metadata = self.connection_metadata.get(sender, {})
        target_client_id = message.get("to")  # Target specific peer
        
        offer_message = {
            "type": "offer",
            "offer": message.get("offer"),
            "from": sender_metadata.get("client_id"),
            "username": sender_metadata.get("username")
        }
        
        # If target specified, send only to that client
        if target_client_id:
            target_ws = self.find_websocket_by_client_id(room_id, target_client_id)
            if target_ws:
                await target_ws.send_text(json.dumps(offer_message))
                logger.info(f"Offer sent from {sender_metadata.get('client_id')} to {target_client_id} in room {room_id}")
            else:
                logger.warning(f"Target client {target_client_id} not found in room {room_id}")
                # Send error back to sender
                await sender.send_text(json.dumps({
                    "type": "error",
                    "message": f"Target client {target_client_id} not found"
                }))
        else:
            # Broadcast to all except sender
            await self.broadcast_to_room(room_id, offer_message, exclude_websocket=sender)
            logger.info(f"Offer broadcast from {sender_metadata.get('client_id')} in room {room_id}")
    
    async def handle_answer(self, room_id: str, sender: WebSocket, message: Dict):
        """Handle WebRTC answer message"""
        sender_metadata = self.connection_metadata.get(sender, {})
        target_client_id = message.get("to")
        
        answer_message = {
            "type": "answer",
            "answer": message.get("answer"),
            "from": sender_metadata.get("client_id"),
            "username": sender_metadata.get("username")
        }
        
        # Answer should go to specific peer who sent the offer
        if target_client_id:
            target_ws = self.find_websocket_by_client_id(room_id, target_client_id)
            if target_ws:
                await target_ws.send_text(json.dumps(answer_message))
                logger.info(f"Answer sent from {sender_metadata.get('client_id')} to {target_client_id} in room {room_id}")
            else:
                logger.warning(f"Target client {target_client_id} not found in room {room_id}")
                # Send error back to sender
                await sender.send_text(json.dumps({
                    "type": "error",
                    "message": f"Target client {target_client_id} not found"
                }))
        else:
            # Fallback: broadcast to all except sender
            await self.broadcast_to_room(room_id, answer_message, exclude_websocket=sender)
            logger.info(f"Answer broadcast from {sender_metadata.get('client_id')} in room {room_id}")
    
    async def handle_ice_candidate(self, room_id: str, sender: WebSocket, message: Dict):
        """Handle ICE candidate message"""
        sender_metadata = self.connection_metadata.get(sender, {})
        target_client_id = message.get("to")
        
        ice_message = {
            "type": "ice_candidate",
            "candidate": message.get("candidate"),
            "from": sender_metadata.get("client_id"),
            "username": sender_metadata.get("username")
        }
        
        # ICE candidates can go to specific peer or broadcast
        if target_client_id:
            target_ws = self.find_websocket_by_client_id(room_id, target_client_id)
            if target_ws:
                await target_ws.send_text(json.dumps(ice_message))
                logger.info(f"ICE candidate sent from {sender_metadata.get('client_id')} to {target_client_id} in room {room_id}")
            else:
                logger.warning(f"Target client {target_client_id} not found in room {room_id}")
        else:
            # Broadcast to all except sender
            await self.broadcast_to_room(room_id, ice_message, exclude_websocket=sender)
            logger.info(f"ICE candidate broadcast from {sender_metadata.get('client_id')} in room {room_id}")
    
    async def handle_ping(self, websocket: WebSocket):
        """Handle ping message"""
        await websocket.send_text(json.dumps({
            "type": "pong"
        }))
    
    def find_websocket_by_client_id(self, room_id: str, client_id: str) -> Optional[WebSocket]:
        """Find WebSocket connection by client ID in a room"""
        if room_id not in self.rooms:
            return None
        
        for ws in self.rooms[room_id]:
            if ws in self.connection_metadata:
                if self.connection_metadata[ws].get("client_id") == client_id:
                    return ws
        
        return None
    
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
