# TURN Server Quick Start

## In 5 Minutes

### 1. Add to .env file

```bash
TURNSERVER_SECRET=your-secret-key-here
TURNSERVER_URLS=["turn:your-turn-server.com:3478", "turns:your-turn-server.com:5349"]
TURNSERVER_TTL=86400
```

### 2. Configure coturn (/etc/turnserver.conf)

```conf
use-auth-secret
static-auth-secret=your-secret-key-here
realm=your-domain.com
listening-port=3478
tls-listening-port=5349
```

### 3. Start coturn

```bash
sudo systemctl start coturn
```

### 4. Use the endpoint

```bash
# Login to get token
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# Get TURN credentials (use token from above)
curl -X GET http://localhost:8000/auth/turn-credentials \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### 5. Use in WebRTC

```javascript
// Get credentials
const response = await fetch('https://localhost:8000/auth/turn-credentials', {
  headers: { 'Authorization': `Bearer ${token}` }
});
const creds = await response.json();

// Use in peer connection
const pc = new RTCPeerConnection({
  iceServers: [{
    urls: creds.urls,
    username: creds.username,
    credential: creds.credential
  }]
});
```

## Test Files

- **Example client**: `examples/turn_credentials_example.html`
- **Tests**: `python3 -m pytest tests/test_turn_credentials.py -v`

## Documentation

- **Setup guide**: `TURN_SERVER_SETUP.md`
- **Implementation details**: `TURN_IMPLEMENTATION_SUMMARY.md`
- **API docs**: `README.md`

## Endpoint

```
GET /auth/turn-credentials
Authorization: Bearer {jwt_token}

Response:
{
  "username": "1704067200:admin",
  "credential": "base64_hmac_sha1",
  "urls": ["turn:server.com:3478", "turns:server.com:5349"],
  "ttl": 86400
}
```

## Files Changed/Added

### Modified
- `env.example` - Added TURN configuration
- `src/utils/config.py` - Added TURN settings
- `src/auth/auth_routes.py` - Added /auth/turn-credentials endpoint
- `README.md` - Added TURN documentation

### Added
- `TURN_SERVER_SETUP.md` - Complete setup guide
- `TURN_IMPLEMENTATION_SUMMARY.md` - Implementation details
- `TURN_QUICKSTART.md` - This file
- `examples/turn_credentials_example.html` - Test client
- `tests/test_turn_credentials.py` - Test suite

## Need Help?

1. Read `TURN_SERVER_SETUP.md` for detailed setup
2. Try `examples/turn_credentials_example.html` in browser
3. Check coturn logs: `sudo journalctl -u coturn -f`
4. Check server logs: `tail -f server.log`


