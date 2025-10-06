# WebRTC Signaling Server

A FastAPI-based signaling server for WebRTC peer-to-peer connections. This server handles the exchange of signaling messages (offers, answers, and ICE candidates) between WebRTC clients.

## Features

### Core Functionality
- WebSocket-based signaling for WebRTC connections
- Room-based connection management
- Real-time message forwarding
- Health check endpoints
- Configurable via environment variables
- Comprehensive logging
- Test coverage

### Security Features
- **JWT Authentication** - Secure token-based authentication
- **CSV User Storage** - Simple file-based user management
- **HTTPS/WSS Only** - Encrypted connections with SSL/TLS
- **DDoS Protection** - Rate limiting and connection tracking
- **CORS Security** - Restricted cross-origin requests
- **Input Validation** - Pydantic model validation
- **Security Logging** - Comprehensive security event logging

## Project Structure

```
EUEM_WEB_RTC_SERVER/
├── src/
│   ├── auth/                       # Authentication system
│   │   ├── __init__.py
│   │   ├── jwt_handler.py          # JWT token management
│   │   └── auth_routes.py          # Authentication endpoints
│   ├── handlers/
│   │   ├── __init__.py
│   │   └── websocket_handler.py    # WebSocket connection management
│   ├── models/
│   │   ├── __init__.py
│   │   └── signal_data.py          # Pydantic models for signaling data
│   ├── security/                   # Security features
│   │   ├── __init__.py
│   │   ├── rate_limiter.py         # DDoS protection & rate limiting
│   │   └── ssl_config.py           # SSL/TLS configuration
│   ├── utils/
│   │   ├── __init__.py
│   │   └── config.py               # Configuration management
│   ├── __init__.py
│   └── main.py                     # Main FastAPI application
├── ssl/                            # SSL certificates (auto-generated)
│   ├── server.crt                  # SSL certificate
│   └── server.key                  # SSL private key
├── tests/
│   └── test_websocket_handler.py   # Unit tests
├── examples/
│   ├── simple_client.html          # Basic client example
│   └── secure_client.html          # Secure client with auth
├── users.csv                       # User credentials (auto-generated)
├── .env                            # Environment configuration
├── requirements.txt                # Python dependencies
├── start_server.sh                 # Basic server startup
├── start_secure_server.sh          # Secure server startup
└── README.md                       # This file
```

## Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd EUEM_WEB_RTC_SERVER
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   python3 -m pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   Edit the `.env` file to match your requirements:
   ```bash
   # Server Configuration
   HOST=0.0.0.0
   PORT=8000
   DEBUG=true
   
   # Security (change in production!)
   SECRET_KEY=your-secret-key-change-this-in-production
   ```

## Usage

### Starting the Server

#### Secure Server (Recommended)
```bash
./start_secure_server.sh
```
- Runs with HTTPS/WSS encryption
- JWT authentication required
- DDoS protection enabled
- Access at `https://localhost:8000`

#### Basic Server (Development Only)
```bash
./start_server.sh
```
- Runs with HTTP/WS (unencrypted)
- No authentication
- Basic rate limiting
- Access at `http://localhost:8000`

#### Manual Startup
```bash
# Secure server
python3 -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --ssl-keyfile ssl/server.key --ssl-certfile ssl/server.crt --reload

# Basic server
python3 -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

### WebSocket Connection

Connect to the signaling server via WebSocket:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/room_name');
```

### API Endpoints

- `GET /` - Health check
- `GET /health` - Detailed health information
- `GET /api/rooms` - List all active rooms
- `POST /api/rooms/{room_id}/info` - Get room information
- `WebSocket /ws/{room_id}` - WebRTC signaling endpoint

### Signaling Message Format

The server expects JSON messages with the following structure:

```json
{
  "type": "offer|answer|ice_candidate|ping",
  "offer": {...},      // For offer messages
  "answer": {...},     // For answer messages
  "candidate": {...}   // For ICE candidate messages
}
```

## Security

### Authentication
The server uses JWT (JSON Web Tokens) for authentication:

1. **Login** - POST to `/auth/login` with username/password
2. **Get Token** - Receive JWT token in response
3. **Connect** - Use token in WebSocket connection
4. **Authenticate** - Server validates token before allowing signaling

### Default Users
The server creates default users on first run:
- `admin` / `admin123`
- `user1` / `password123`
- `user2` / `password123`

**Important**: Change these passwords in production!

### SSL/TLS
- Auto-generates self-signed certificates for development
- Uses HTTPS/WSS for all connections
- Supports production certificates
- Enforces secure cipher suites

### DDoS Protection
- Rate limiting: 60 messages/minute per IP
- Connection tracking: Max 5 connections per IP
- Authentication failure tracking
- IP blocking after repeated failures
- Automatic cleanup of blocked IPs

### Security Headers
- CORS restrictions
- Secure cookie settings
- XSS protection
- Content type validation

## Configuration

All configuration is handled through environment variables in the `.env` file:

### Server Configuration
| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Server host |
| `PORT` | `8000` | Server port |
| `DEBUG` | `false` | Debug mode |
| `REQUIRE_HTTPS` | `true` | Force HTTPS/WSS connections |

### Security Configuration
| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | `your-secret-key-here` | General secret key |
| `JWT_SECRET_KEY` | `your-jwt-secret-key` | JWT signing key |
| `CORS_ORIGINS` | `https://localhost:3000` | Allowed origins |
| `RATE_LIMIT_PER_MINUTE` | `60` | Rate limit per IP |

### WebSocket Configuration
| Variable | Default | Description |
|----------|---------|-------------|
| `WEBSOCKET_TIMEOUT` | `30` | WebSocket timeout in seconds |
| `MAX_CONNECTIONS_PER_ROOM` | `10` | Maximum connections per room |

## Development

### Running Tests

```bash
pytest tests/
```

### Code Structure

- **WebSocketHandler**: Manages WebSocket connections and message routing
- **SignalData Models**: Pydantic models for message validation
- **Config**: Environment-based configuration management
- **Main App**: FastAPI application with WebSocket endpoints

### Adding New Features

1. Add new message types to `src/models/signal_data.py`
2. Implement handlers in `src/handlers/websocket_handler.py`
3. Add tests in `tests/`
4. Update documentation

## Production Deployment

1. Set `DEBUG=false` in `.env`
2. Change `SECRET_KEY` to a secure value
3. Configure proper `CORS_ORIGINS`
4. Use a production WSGI server like Gunicorn:
   ```bash
   gunicorn src.main:app -w 4 -k uvicorn.workers.UvicornWorker
   ```

## WebRTC Client Integration

Here's a basic example of how to integrate with the signaling server:

```javascript
// Connect to signaling server
const ws = new WebSocket('ws://localhost:8000/ws/room_name');

// Handle incoming messages
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  
  switch(message.type) {
    case 'offer':
      // Handle WebRTC offer
      break;
    case 'answer':
      // Handle WebRTC answer
      break;
    case 'ice_candidate':
      // Handle ICE candidate
      break;
  }
};

// Send offer
ws.send(JSON.stringify({
  type: 'offer',
  offer: peerConnection.localDescription
}));
```

## 🔐 Security

**Important:** This server handles sensitive data including user credentials and SSL certificates. Please read the [Security Setup Guide](SECURITY_SETUP.md) before deployment.

### Quick Security Checklist:
- [ ] Copy `env.example` to `.env` and update secrets
- [ ] Change default passwords in `users.csv`
- [ ] Use real SSL certificates for production
- [ ] Set `REQUIRE_HTTPS=true` for production
- [ ] Limit `CORS_ORIGINS` to your domains

See [SECURITY_SETUP.md](SECURITY_SETUP.md) for detailed security instructions.

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]
