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

    @pytest.mark.asyncio
    async def test_disconnect(self, handler, mock_websocket):
        """Test WebSocket disconnection"""
        room_id = "test_room"

        # Connect first
        await handler.connect(mock_websocket, room_id)

        # Then disconnect
        await handler.disconnect(mock_websocket, room_id)

        assert mock_websocket not in handler.connection_metadata
        assert room_id not in handler.rooms

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
        mock_websocket2.send_text = AsyncMock()

        await handler.connect(mock_websocket, room_id, username="user1", client_id="client1")
        await handler.connect(mock_websocket2, room_id, username="user2", client_id="client2")

        # Handle offer
        await handler.handle_message(room_id, mock_websocket, offer_message)

        mock_websocket2.send_text.assert_called()

    @pytest.mark.asyncio
    async def test_handle_ice_candidate(self, handler, mock_websocket):
        """Test handling ICE candidate message"""
        room_id = "test_room"
        candidate_message = {
            "type": "ice_candidate",
            "candidate": {"candidate": "candidate_data"}
        }

        mock_websocket2 = AsyncMock()
        mock_websocket2.send_text = AsyncMock()

        await handler.connect(mock_websocket, room_id, username="user1", client_id="client1")
        await handler.connect(mock_websocket2, room_id, username="user2", client_id="client2")

        await handler.handle_message(room_id, mock_websocket, candidate_message)

        mock_websocket2.send_text.assert_called()

    @pytest.mark.asyncio
    async def test_handle_ping(self, handler, mock_websocket):
        """Test ping handling"""
        await handler.handle_ping(mock_websocket)
        mock_websocket.send_text.assert_called_once_with(json.dumps({
            "type": "pong"
        }))
