# WebRTC Signaling Server

A FastAPI-based signaling server for WebRTC peer-to-peer connections. This server handles the exchange of signaling messages (offers, answers, and ICE candidates) between WebRTC clients with enterprise-grade security features.

## Features

### Core Functionality
- WebSocket-based signaling for WebRTC connections
- Room-based connection management
- Real-time message forwarding with targeted messaging
- Client ID tracking for peer-to-peer connections
- Health check endpoints
- Configurable via environment variables
- Comprehensive logging
- Test coverage

### Security Features
- **JWT Authentication** - Secure token-based authentication
- **CSV User Storage** - Simple file-based user management with bcrypt password hashing
- **HTTPS/WSS Only** - Encrypted connections with SSL/TLS
- **DDoS Protection** - Rate limiting and connection tracking
- **CORS Security** - Restricted cross-origin requests
- **Input Validation** - Pydantic model validation
- **Security Logging** - Comprehensive security event logging
- **TURN Server Integration** - Time-limited credentials for coturn TURN servers

### WebSocket Improvements
- Client ID tracking and management
- Existing users list sent on room join
- Targeted peer-to-peer messaging
- No echo to sender (messages not sent back to originator)
- Sender information included in all messages
- Helper methods for client lookup

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
│   ├── test_websocket_handler.py   # WebSocket handler tests
│   └── test_turn_credentials.py    # TURN credentials tests
├── examples/
│   ├── simple_client.html          # Basic client example
│   ├── secure_client.html          # Secure client with auth
│   └── turn_credentials_example.html # TURN credentials example
├── users.csv                       # User credentials (auto-generated)
├── .env                            # Environment configuration
├── requirements.txt                # Python dependencies
├── start_dev.sh                    # Development server startup (HTTP)
├── start_prod.sh                   # Production server startup (behind nginx)
└── README.md                       # This file
```

## Installation

### 1. Clone the repository
```bash
git clone <repository-url>
cd EUEM_WEB_RTC_SERVER
```

### 2. Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies
```bash
python3 -m pip install -r requirements.txt
```

### 4. Configure environment variables
Copy the example environment file and edit it:
```bash
cp env.example .env
nano .env
```

**Important**: Change these values in production:
- `SECRET_KEY` - Use a strong 256-bit secret
- `JWT_SECRET_KEY` - Use a different strong secret for JWT signing
- `CORS_ORIGINS` - Limit to your actual domains
- `REQUIRE_HTTPS=true` - Enable HTTPS enforcement

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
| `CORS_ORIGINS` | `["*"]` | Allowed origins (`["*"]` allows all, or specify array of URLs) |
| `CORS_ALLOW_CREDENTIALS` | `true` | Allow credentials in CORS requests |
| `RATE_LIMIT_PER_MINUTE` | `60` | Rate limit per IP |

### WebSocket Configuration
| Variable | Default | Description |
|----------|---------|-------------|
| `WEBSOCKET_TIMEOUT` | `30` | WebSocket timeout in seconds |
| `MAX_CONNECTIONS_PER_ROOM` | `10` | Maximum connections per room |

### TURN Server Configuration
| Variable | Default | Description |
|----------|---------|-------------|
| `TURNSERVER_SECRET` | `""` | Shared secret for TURN server (coturn) |
| `TURNSERVER_URL` | `""` | Primary TURN server URL (e.g., `turn:turn.example.com:3478`) |
| `TURNSERVER_URLS` | `[]` | List of TURN server URLs (supports TURN and TURNS) |
| `TURNSERVER_TTL` | `86400` | Credential validity period in seconds (default: 24 hours) |

### CORS Configuration Options

**Option 1: Allow All Origins (Recommended for Multiple Clients)**

When you have multiple clients connecting from different addresses:
```bash
CORS_ORIGINS=["*"]
CORS_ALLOW_CREDENTIALS=true
```

This allows clients to connect from any domain or IP address.

**Option 2: Restrict to Specific Domains**

When you know the exact domains clients will use:
```bash
CORS_ORIGINS=["https://yourdomain.com", "https://app.yourdomain.com"]
CORS_ALLOW_CREDENTIALS=true
```

**Security Note**: JWT authentication still protects your server even with `CORS_ORIGINS=["*"]`. Only authenticated users with valid tokens can access the signaling server. CORS restrictions are primarily a browser security feature, and WebRTC applications often require flexible CORS due to peer-to-peer nature.

### Example Production .env
```bash
HOST=0.0.0.0
PORT=8000
DEBUG=false
REQUIRE_HTTPS=true

# Allow all origins for flexible client access
CORS_ORIGINS=["*"]
CORS_ALLOW_CREDENTIALS=true

SECRET_KEY=your-256-bit-secret-key-here
JWT_SECRET_KEY=your-different-jwt-secret-key-here
LOG_LEVEL=INFO
RATE_LIMIT_PER_MINUTE=60

# TURN Server Configuration
TURNSERVER_SECRET=your-shared-secret-here
TURNSERVER_URLS=["turn:turn.example.com:3478", "turns:turn.example.com:5349"]
TURNSERVER_TTL=86400
```

## Security Setup

### Sensitive Files Protection

The following sensitive files are automatically ignored by git:

#### SSL/TLS Certificates
- `ssl/` directory and all contents
- `*.crt`, `*.key`, `*.pem`, `*.p12`, `*.pfx` files

#### User Data
- `users.csv` - Contains user credentials and password hashes
- `user_data/` directory
- `auth_data/` directory

#### Configuration Files
- `.env` - Environment variables with secrets
- `config.ini` - Configuration with sensitive data
- `secrets.json` - JSON configuration with secrets

### Initial Setup Steps

#### 1. SSL Certificates (for HTTPS/WSS)

For production, nginx handles SSL/TLS termination and proxies to your FastAPI application. This provides easier certificate management with certbot and better performance.

See "Production Deployment with Nginx" section below for setup instructions.

For development (HTTP only, no SSL needed):
```bash
./start_dev.sh
```

#### 2. User Management

Default users are created automatically in `users.csv`:
- `admin` / `admin123`
- `user1` / `password123`
- `user2` / `password123`

**Important**: Change these passwords in production!

##### User Management Script

A convenient Python script is provided to add or remove users from the CSV file:

**Add a user**:
```bash
python manage_users.py add username:password
```

**Add a user with custom email**:
```bash
python manage_users.py add username:password:email@example.com
```

**Remove a user**:
```bash
python manage_users.py remove username
```

**List all users**:
```bash
python manage_users.py list
```

**Examples**:
```bash
# Add a new user
python manage_users.py add alice:securePassword123

# Add a user with custom email
python manage_users.py add bob:anotherSecure456:bob@company.com

# Remove a user
python manage_users.py remove alice

# List all users
python manage_users.py list
```

The script automatically:
- Hashes passwords using bcrypt (same as the authentication system)
- Generates default email addresses (`username@example.com`) if not specified
- Validates username (minimum 3 characters) and password (minimum 6 characters)
- Prevents duplicate usernames
- Sets users as active by default

#### 3. File Permissions

Secure sensitive files:
```bash
chmod 600 .env
chmod 600 ssl/server.key
chmod 644 ssl/server.crt
chmod 644 users.csv
```

### Security Checklist

Before deploying to production:

- [ ] Changed all default passwords in `users.csv`
- [ ] Updated `SECRET_KEY` in `.env`
- [ ] Updated `JWT_SECRET_KEY` in `.env`
- [ ] Set `REQUIRE_HTTPS=true`
- [ ] Limited `CORS_ORIGINS` to actual domains
- [ ] Installed real SSL certificates
- [ ] Set appropriate file permissions
- [ ] Reviewed and removed any test/debug code
- [ ] Enabled proper logging and monitoring

### Security Best Practices

#### Development
- Use `REQUIRE_HTTPS=false` for local development
- Self-signed certificates are acceptable for local testing
- Default passwords are acceptable for development only

#### Production
- **ALWAYS** use `REQUIRE_HTTPS=true`
- **ALWAYS** use real SSL certificates from a trusted CA
- **ALWAYS** change all default passwords
- **ALWAYS** use strong, unique secrets in `.env`
- **ALWAYS** limit `CORS_ORIGINS` to your actual domains
- **ALWAYS** use a secure password hashing method (bcrypt is enabled)

## Usage

### Starting the Server

#### Production Server (Behind Nginx)
```bash
./start_prod.sh
```
- Runs on HTTP at `http://127.0.0.1:8000` (localhost only)
- Nginx handles HTTPS/WSS encryption
- JWT authentication required
- Requires nginx configured with SSL certificates
- Requires `users.csv` with production credentials
- DDoS protection enabled
- Access via nginx at `https://your-domain.com`

#### Development Server (HTTP/WS)
```bash
./start_dev.sh
```
- Runs with HTTP/WS (unencrypted)
- Auto-creates test users if not exists
- Enables auto-reload for code changes
- Debug logging enabled
- Access at `http://localhost:8000`
- Test credentials provided on startup

#### Manual Startup
```bash
# Production server (behind nginx)
python3 -m uvicorn src.main:app --host 127.0.0.1 --port 8000 --log-level info

# Development server (HTTP)
python3 -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload --log-level debug
```

### API Endpoints

#### General
- `GET /` - Health check
- `GET /health` - Detailed health information
- `GET /api/rooms` - List all active rooms
- `POST /api/rooms/{room_id}/info` - Get room information
- `WebSocket /ws/{room_id}` - WebRTC signaling endpoint

#### Authentication
- `POST /auth/login` - Login and get JWT token
- `POST /auth/token` - OAuth2 compatible token endpoint
- `GET /auth/me` - Get current user information
- `POST /auth/refresh` - Refresh JWT token
- `POST /auth/logout` - Logout
- `GET /auth/turn-credentials` - Get TURN server credentials (requires authentication)

### WebSocket Connection Flow

#### 1. Connect to WebSocket
```javascript
const ws = new WebSocket('wss://localhost:8000/ws/room_name');
```

#### 2. Authentication Flow
```javascript
// Server sends authentication requirement
// {"type": "auth_required"}

// Client sends JWT token and optional client ID
ws.send(JSON.stringify({
  type: "auth_token",
  token: jwtToken,
  clientId: clientId  // Optional, server generates if not provided
}));

// Server responds with success
// {"type": "auth_success", "user": "username", "client_id": "uuid"}

// Server sends list of existing users in room
// {"type": "users_in_room", "users": [{"client_id": "...", "username": "..."}]}

// Server broadcasts to others that you joined
// {"type": "user_joined", "username": "...", "client_id": "..."}
```

### Signaling Message Format

#### Offer (with targeted messaging)
```javascript
// Send offer to specific peer
ws.send(JSON.stringify({
  type: "offer",
  offer: peerConnection.localDescription,
  to: targetClientId  // Optional: if omitted, broadcasts to all
}));

// Recipient receives:
// {
//   "type": "offer",
//   "offer": {...},
//   "from": senderClientId,
//   "username": senderUsername
// }
```

#### Answer
```javascript
ws.send(JSON.stringify({
  type: "answer",
  answer: peerConnection.localDescription,
  to: targetClientId
}));
```

#### ICE Candidate
```javascript
ws.send(JSON.stringify({
  type: "ice_candidate",
  candidate: candidateData,
  to: targetClientId
}));
```

## TURN Server Integration

TURN (Traversal Using Relays around NAT) enables WebRTC connections to work even when direct peer-to-peer connections are blocked by firewalls or NAT.

### Quick Start with TURN

#### 1. Install coturn

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install coturn
```

**CentOS/RHEL:**
```bash
sudo yum install coturn
```

**macOS:**
```bash
brew install coturn
```

#### 2. Configure coturn

Edit `/etc/turnserver.conf`:
```conf
# TURN server name and realm
realm=your-domain.com
server-name=your-domain.com

# Listening ports
listening-port=3478
tls-listening-port=5349

# IP addresses
listening-ip=0.0.0.0
relay-ip=YOUR_SERVER_PUBLIC_IP
external-ip=YOUR_SERVER_PUBLIC_IP

# Enable time-limited credentials
use-auth-secret
static-auth-secret=YOUR_TURNSERVER_SECRET

# Certificate files (for TURNS - TLS)
cert=/path/to/cert.pem
pkey=/path/to/privkey.pem

# Security options
fingerprint
lt-cred-mech
no-loopback-peers

# Logging
log-file=/var/log/turnserver.log
verbose
```

#### 3. Generate Shared Secret
```bash
openssl rand -hex 32
```

Use this value for both:
- `static-auth-secret` in `/etc/turnserver.conf`
- `TURNSERVER_SECRET` in your `.env` file

#### 4. Update .env file
```bash
TURNSERVER_SECRET=your-shared-secret-here
TURNSERVER_URLS=["turn:turn.example.com:3478", "turns:turn.example.com:5349"]
TURNSERVER_TTL=86400
```

#### 5. Start coturn
```bash
sudo systemctl enable coturn
sudo systemctl start coturn
```

#### 6. Configure Firewall

**UFW (Ubuntu):**
```bash
sudo ufw allow 3478/tcp
sudo ufw allow 3478/udp
sudo ufw allow 5349/tcp
sudo ufw allow 5349/udp
sudo ufw allow 49152:65535/udp  # Relay ports
```

### Using TURN Credentials in Your Application

#### 1. Login and Get JWT Token
```javascript
const response = await fetch('https://localhost:8000/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ username: 'admin', password: 'admin123' })
});
const { access_token } = await response.json();
```

#### 2. Get TURN Credentials
```javascript
const turnResponse = await fetch('https://localhost:8000/auth/turn-credentials', {
  method: 'GET',
  headers: { 'Authorization': `Bearer ${access_token}` }
});
const turnCredentials = await turnResponse.json();
// Response: { username, credential, urls, ttl }
```

#### 3. Create RTCPeerConnection with TURN
```javascript
const configuration = {
  iceServers: [
    {
      urls: turnCredentials.urls,
      username: turnCredentials.username,
      credential: turnCredentials.credential
    },
    // Optional: Add STUN servers
    {
      urls: 'stun:stun.l.google.com:19302'
    }
  ]
};

const peerConnection = new RTCPeerConnection(configuration);
```

### TURN Credentials Format

The server generates credentials compatible with coturn TURN server:
- **Username format**: `timestamp:username` (e.g., `1704067200:admin`)
- **Credential**: HMAC-SHA1 hash encoded in base64
- **TTL**: Credentials expire after the configured TTL (default: 24 hours)
- **URLs**: List of TURN/TURNS server URLs

### TURN API Reference

#### GET /auth/turn-credentials

**Description**: Generate time-limited TURN server credentials

**Authentication**: Required (JWT Bearer token)

**Request Headers**:
```
Authorization: Bearer {jwt_token}
```

**Response** (200 OK):
```json
{
  "username": "1704067200:admin",
  "credential": "dGVzdF9jcmVkZW50aWFs...",
  "urls": [
    "turn:turn.example.com:3478",
    "turns:turn.example.com:5349"
  ],
  "ttl": 86400
}
```

**Error Responses**:
- `401 Unauthorized`: Missing or invalid JWT token
- `503 Service Unavailable`: TURN server not configured

### TURN Production Recommendations

1. **Use dedicated server**: Don't run TURN on the same server as the signaling server
2. **Enable monitoring**: Use Prometheus or similar tools
3. **Set resource limits**: Configure `max-bps` and `total-quota`
4. **Use TURNS**: Always provide TURNS (TLS) option for security
5. **Geographic distribution**: Deploy TURN servers in multiple regions
6. **Load balancing**: Use multiple TURN servers for redundancy
7. **Regular updates**: Keep coturn updated for security patches
8. **Monitor costs**: TURN servers can consume significant bandwidth

### SSL/TLS Certificates for TURNS

Using Let's Encrypt:
```bash
# Install certbot
sudo apt-get install certbot

# Get certificate
sudo certbot certonly --standalone -d turn.your-domain.com

# Update turnserver.conf
cert=/etc/letsencrypt/live/turn.your-domain.com/cert.pem
pkey=/etc/letsencrypt/live/turn.your-domain.com/privkey.pem

# Auto-renewal
sudo certbot renew --dry-run
```

### TURN Troubleshooting

#### "TURN server not configured"
**Cause**: `TURNSERVER_SECRET` is empty in .env
**Solution**: Set `TURNSERVER_SECRET` in your .env file

#### "Authentication failed" in coturn logs
**Cause**: Secret mismatch between server and coturn
**Solution**: Ensure `TURNSERVER_SECRET` matches `static-auth-secret` in coturn config

#### Credentials expire immediately
**Cause**: Server time not synchronized
**Solution**: Ensure both servers have correct time (use NTP)

#### Can't connect to TURN server
**Cause**: Firewall blocking TURN ports
**Solution**: Open ports 3478 (TURN) and 5349 (TURNS) in firewall

## WebSocket Client Implementation

### Basic Client Example

```javascript
// Generate client ID (optional)
const myClientId = crypto.randomUUID();

// Connect to signaling server
const ws = new WebSocket('wss://localhost:8000/ws/room_name');

ws.onopen = () => {
  // Wait for auth_required message
};

ws.onmessage = async (event) => {
  const message = JSON.parse(event.data);
  
  switch(message.type) {
    case 'auth_required':
      // Send authentication
      ws.send(JSON.stringify({
        type: 'auth_token',
        token: jwtToken,
        clientId: myClientId  // Optional
      }));
      break;
      
    case 'auth_success':
      console.log('Connected as:', message.user);
      console.log('My client ID:', message.client_id);
      break;
      
    case 'users_in_room':
      // List of existing users
      console.log('Users in room:', message.users);
      // Each user: {client_id, username}
      break;
      
    case 'user_joined':
      console.log('User joined:', message.username, message.client_id);
      break;
      
    case 'user_left':
      console.log('User left:', message.username, message.client_id);
      break;
      
    case 'offer':
      // Handle WebRTC offer from specific peer
      const senderClientId = message.from;
      const senderUsername = message.username;
      await handleOffer(message.offer, senderClientId);
      break;
      
    case 'answer':
      // Handle WebRTC answer
      await handleAnswer(message.answer, message.from);
      break;
      
    case 'ice_candidate':
      // Handle ICE candidate
      await handleCandidate(message.candidate, message.from);
      break;
  }
};

// Send offer to specific peer
function sendOffer(targetClientId, offer) {
  ws.send(JSON.stringify({
    type: 'offer',
    offer: offer,
    to: targetClientId
  }));
}

// Send answer to specific peer
function sendAnswer(targetClientId, answer) {
  ws.send(JSON.stringify({
    type: 'answer',
    answer: answer,
    to: targetClientId
  }));
}

// Send ICE candidate to specific peer
function sendCandidate(targetClientId, candidate) {
  ws.send(JSON.stringify({
    type: 'ice_candidate',
    candidate: candidate,
    to: targetClientId
  }));
}
```

### Client Features

1. **Client ID Tracking**: Each client gets a unique ID for peer-to-peer messaging
2. **Existing Users List**: New users receive list of existing users on join
3. **Targeted Messaging**: Send offers, answers, and candidates to specific peers
4. **No Echo**: Senders never receive their own messages
5. **Sender Information**: All messages include sender's client_id and username

## Development

### Running Tests

```bash
# All tests
pytest tests/

# Specific test file
python3 -m pytest tests/test_turn_credentials.py -v
python3 -m pytest tests/test_websocket_handler.py -v
```

### Code Structure

- **WebSocketHandler**: Manages WebSocket connections and message routing
- **SignalData Models**: Pydantic models for message validation
- **JWT Handler**: User authentication and token management
- **Config**: Environment-based configuration management
- **Main App**: FastAPI application with WebSocket endpoints

### Adding New Features

1. Add new message types to `src/models/signal_data.py`
2. Implement handlers in `src/handlers/websocket_handler.py`
3. Add tests in `tests/`
4. Update documentation

### Performance Impact

The security features add minimal overhead:
- **JWT validation**: ~1ms per request
- **Rate limiting**: ~0.1ms per request
- **SSL/TLS**: ~5-10ms connection overhead
- **Password hashing**: ~100ms (only during login)
- **Memory usage**: +~10MB for security tracking

## Production Deployment

### Deployment with Nginx

Production deployments use nginx for SSL/TLS termination and reverse proxying to your FastAPI application.

#### 1. Install Nginx

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install nginx
```

**CentOS/RHEL:**
```bash
sudo yum install nginx
```

#### 2. Obtain SSL Certificates with Certbot

**Install certbot:**
```bash
# Ubuntu/Debian
sudo apt-get install certbot python3-certbot-nginx

# CentOS/RHEL
sudo yum install certbot python3-certbot-nginx
```

**Get certificate:**
```bash
# Stop nginx temporarily
sudo systemctl stop nginx

# Obtain certificate (replace with your domain)
sudo certbot certonly --standalone -d webrtc.yourdomain.com

# Start nginx
sudo systemctl start nginx
```

Certificates will be saved to:
- Certificate: `/etc/letsencrypt/live/webrtc.yourdomain.com/fullchain.pem`
- Private Key: `/etc/letsencrypt/live/webrtc.yourdomain.com/privkey.pem`

#### 3. Configure Nginx

Create nginx configuration file:
```bash
sudo nano /etc/nginx/sites-available/webrtc-signaling
```

Add this configuration (replace `your-domain.com` with your actual domain):

```nginx
# Redirect HTTP to HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name your-domain.com;
    
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }
    
    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS server with WebSocket support
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name your-domain.com;
    
    # SSL certificates (managed by certbot)
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers off;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # Proxy to FastAPI
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts for WebSocket
        proxy_read_timeout 86400;
        proxy_send_timeout 86400;
    }
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/webrtc-signaling /etc/nginx/sites-enabled/
```

Test nginx configuration:
```bash
sudo nginx -t
```

Reload nginx:
```bash
sudo systemctl reload nginx
```

#### 4. Configure Environment Variables

Update your `.env` file:
```bash
HOST=127.0.0.1          # Listen on localhost only
PORT=8000               # Port for FastAPI
REQUIRE_HTTPS=false     # Nginx handles HTTPS
DEBUG=false             # Production mode

# Change these to secure values
SECRET_KEY=your-256-bit-secret-key
JWT_SECRET_KEY=your-different-256-bit-jwt-key

# Update with your domain or use ["*"] for all origins
CORS_ORIGINS=["https://yourdomain.com"]
```

#### 5. Start the Application

```bash
./start_prod.sh
```

Your server will be running on `http://127.0.0.1:8000` (not accessible from outside).
Access it via nginx at `https://yourdomain.com`.

#### 6. Set Up Auto-Renewal for SSL Certificates

Test renewal:
```bash
sudo certbot renew --dry-run
```

Enable automatic renewal:
```bash
# Certbot timer is usually enabled by default on Ubuntu
sudo systemctl status certbot.timer

# If not enabled:
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
```

#### 7. Create Systemd Service (Optional but Recommended)

Create a systemd service file:
```bash
sudo nano /etc/systemd/system/webrtc-signaling.service
```

Add this content:
```ini
[Unit]
Description=WebRTC Signaling Server
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/EUEM_WEB_RTC_SERVER
Environment="PATH=/path/to/EUEM_WEB_RTC_SERVER/venv/bin"
ExecStart=/path/to/EUEM_WEB_RTC_SERVER/venv/bin/python3 -m uvicorn src.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable webrtc-signaling
sudo systemctl start webrtc-signaling
sudo systemctl status webrtc-signaling
```

#### Testing Your Deployment

```bash
# Test health endpoint
curl https://yourdomain.com/health

# Test WebSocket (requires wscat: npm install -g wscat)
wscat -c wss://yourdomain.com/ws/testroom

# Check nginx logs
sudo tail -f /var/log/nginx/webrtc-signaling-access.log
sudo tail -f /var/log/nginx/webrtc-signaling-error.log

# Check application logs
tail -f server.log
```

### Pre-deployment Checklist

1. **Security**
   - [ ] Set `DEBUG=false` in `.env`
   - [ ] Change `SECRET_KEY` to a secure value
   - [ ] Change `JWT_SECRET_KEY` to a secure value
   - [ ] Configure proper `CORS_ORIGINS`
   - [ ] Obtain SSL certificates (via certbot)
   - [ ] Configure nginx properly
   - [ ] Change all default passwords in `users.csv`
   - [ ] Set `HOST=127.0.0.1` when behind nginx
   - [ ] Set `REQUIRE_HTTPS=false` when behind nginx

2. **TURN Server**
   - [ ] Set strong `TURNSERVER_SECRET`
   - [ ] Configure coturn with same secret
   - [ ] Use HTTPS/TURNS for encrypted connections
   - [ ] Configure SSL certificates for TURNS
   - [ ] Open firewall ports (3478, 5349, relay ports)
   - [ ] Set appropriate `TURNSERVER_TTL`
   - [ ] Monitor coturn logs for abuse
   - [ ] Use multiple TURN servers for redundancy

3. **Monitoring**
   - [ ] Configure proper logging
   - [ ] Set up log rotation
   - [ ] Monitor authentication failures
   - [ ] Track connection statistics
   - [ ] Set up alerts for security events

### Using Production WSGI Server

```bash
# Using Gunicorn with Uvicorn workers
gunicorn src.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Monitoring

Monitor these files for security:
- `server.log` - Check for authentication failures
- `access.log` - Monitor for suspicious requests
- `users.csv` - Regular user access reviews
- `/var/log/turnserver.log` - TURN server activity

## Example Files

The project includes several example files to help you get started:

- **examples/simple_client.html** - Basic client example without authentication
- **examples/secure_client.html** - Secure client with JWT authentication
- **examples/turn_credentials_example.html** - Interactive TURN credentials test client

Open any example in your browser and follow the on-screen instructions.

## Resources

- coturn GitHub: https://github.com/coturn/coturn
- WebRTC samples: https://webrtc.github.io/samples/
- TURN RFC: https://tools.ietf.org/html/rfc5766
- FastAPI documentation: https://fastapi.tiangolo.com/

## Important Notes

1. **Never commit** `.env`, `users.csv`, or `ssl/` files to git
2. **Never share** private keys or passwords
3. **Regularly rotate** secrets and passwords
4. **Monitor logs** for security issues
5. **Keep dependencies** updated for security patches

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]
