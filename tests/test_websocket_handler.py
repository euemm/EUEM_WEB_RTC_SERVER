"""
Tests for WebSocket Handler
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock
from src.handlers.websocket_handler import WebSocketHandler

class TestWebSocketHandler:
    
    @pytest.fixture
    def handler(self):
        return WebSocketHandler()
    
    @pytest.fixture
    def mock_websocket(self):
        websocket = AsyncMock()
        websocket.accept = AsyncMock()
        websocket.send_text = AsyncMock()
        websocket.receive_text = AsyncMock()
        return websocket
    
    @pytest.mark.asyncio
    async def test_connect(self, handler, mock_websocket):
        """Test WebSocket connection"""
        room_id = "test_room"
        
        await handler.connect(mock_websocket, room_id)
        
        assert room_id in handler.rooms
        assert mock_websocket in handler.rooms[room_id]
        assert mock_websocket in handler.connection_metadata
        mock_websocket.accept.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_disconnect(self, handler, mock_websocket):
        """Test WebSocket disconnection"""
        room_id = "test_room"
        
        # Connect first
        await handler.connect(mock_websocket, room_id)
        
        # Then disconnect
        await handler.disconnect(mock_websocket, room_id)
        
        assert mock_websocket not in handler.rooms[room_id]
        assert mock_websocket not in handler.connection_metadata
    
    @pytest.mark.asyncio
    async def test_handle_offer(self, handler, mock_websocket):
        """Test handling offer message"""
        room_id = "test_room"
        offer_message = {
            "type": "offer",
            "offer": {"sdp": "test_sdp", "type": "offer"}
        }
        
        # Add another mock websocket to the room
        mock_websocket2 = AsyncMock()
        handler.rooms[room_id] = {mock_websocket, mock_websocket2}
        
        await handler.handle_offer(room_id, mock_websocket, offer_message)
        
        # Check that the offer was sent to the other websocket
        mock_websocket2.send_text.assert_called_once()
        sent_data = json.loads(mock_websocket2.send_text.call_args[0][0])
        assert sent_data["type"] == "offer"
        assert sent_data["offer"] == offer_message["offer"]
