# TURN Server Setup Guide

This guide explains how to set up and configure a coturn TURN server to work with the WebRTC Signaling Server.

## What is TURN?

TURN (Traversal Using Relays around NAT) is a protocol that allows WebRTC connections to work even when direct peer-to-peer connections are blocked by firewalls or NAT. A TURN server acts as a relay for media traffic when direct connections fail.

## Why Use TURN?

- Works behind restrictive firewalls
- Enables connections through symmetric NAT
- Ensures connectivity in corporate networks
- Fallback when STUN fails

## Installing coturn

### Ubuntu/Debian

```bash
sudo apt-get update
sudo apt-get install coturn
```

### CentOS/RHEL

```bash
sudo yum install coturn
```

### macOS (using Homebrew)

```bash
brew install coturn
```

### From Source

```bash
git clone https://github.com/coturn/coturn.git
cd coturn
./configure
make
sudo make install
```

## Configuring coturn

### 1. Edit coturn configuration

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

# External IP (important for servers behind NAT)
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

# Logging
log-file=/var/log/turnserver.log
verbose

# Performance tuning
total-quota=100
max-bps=1000000

# Deny loopback addresses
no-loopback-peers

# Enable Prometheus monitoring (optional)
# prometheus
```

### 2. Key Configuration Parameters

#### Required Settings

- `use-auth-secret`: Enable time-limited credentials
- `static-auth-secret`: Shared secret (must match `TURNSERVER_SECRET` in .env)
- `realm`: Your domain name
- `listening-ip`: Server IP address (use 0.0.0.0 for all interfaces)
- `external-ip`: Public IP address (for servers behind NAT)

#### Optional but Recommended

- `cert` and `pkey`: SSL certificates for TURNS (TLS)
- `max-bps`: Bandwidth limit per allocation
- `total-quota`: Maximum number of allocations
- `fingerprint`: Enable DTLS fingerprint
- `no-loopback-peers`: Security measure

### 3. Generate Shared Secret

Generate a strong shared secret for your TURN server:

```bash
openssl rand -hex 32
```

Use this value for both:
- `static-auth-secret` in `/etc/turnserver.conf`
- `TURNSERVER_SECRET` in your `.env` file

## Configuring the Signaling Server

### 1. Update .env file

```bash
# TURN Server Configuration
TURNSERVER_SECRET=YOUR_SHARED_SECRET_HERE
TURNSERVER_URL=turn:your-turn-server.com:3478
TURNSERVER_URLS=["turn:your-turn-server.com:3478", "turns:your-turn-server.com:5349"]
TURNSERVER_TTL=86400
```

### 2. Configuration Parameters

- `TURNSERVER_SECRET`: Shared secret (must match coturn config)
- `TURNSERVER_URL`: Primary TURN server URL (used if TURNSERVER_URLS is empty)
- `TURNSERVER_URLS`: List of TURN server URLs (supports multiple servers and protocols)
- `TURNSERVER_TTL`: Credential validity period in seconds (default: 86400 = 24 hours)

### 3. URL Formats

**TURN (UDP/TCP)**:
```
turn:your-turn-server.com:3478
turn:your-turn-server.com:3478?transport=tcp
```

**TURNS (TLS)**:
```
turns:your-turn-server.com:5349
turns:your-turn-server.com:5349?transport=tcp
```

**Multiple URLs Example**:
```bash
TURNSERVER_URLS=["turn:turn1.example.com:3478", "turn:turn2.example.com:3478", "turns:turn1.example.com:5349"]
```

## Starting coturn

### Using systemd (Ubuntu/Debian)

```bash
# Enable coturn
sudo systemctl enable coturn

# Start coturn
sudo systemctl start coturn

# Check status
sudo systemctl status coturn

# View logs
sudo journalctl -u coturn -f
```

### Manual start

```bash
sudo turnserver -c /etc/turnserver.conf
```

### Testing coturn

Test if your TURN server is working:

```bash
# Install trickle-ice tool
npm install -g trickle-ice

# Test your TURN server
trickle-ice --turn turn:your-turn-server.com:3478 --username test --password test
```

Or use online tester: https://webrtc.github.io/samples/src/content/peerconnection/trickle-ice/

## Firewall Configuration

### Allow TURN traffic

```bash
# UFW (Ubuntu)
sudo ufw allow 3478/tcp
sudo ufw allow 3478/udp
sudo ufw allow 5349/tcp
sudo ufw allow 5349/udp
sudo ufw allow 49152:65535/udp  # Relay ports
```

```bash
# iptables
sudo iptables -A INPUT -p tcp --dport 3478 -j ACCEPT
sudo iptables -A INPUT -p udp --dport 3478 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 5349 -j ACCEPT
sudo iptables -A INPUT -p udp --dport 5349 -j ACCEPT
sudo iptables -A INPUT -p udp --dport 49152:65535 -j ACCEPT
```

### Cloud Provider Firewall

Don't forget to configure security groups/firewall rules in your cloud provider:
- AWS: Security Groups
- Google Cloud: Firewall Rules
- Azure: Network Security Groups
- DigitalOcean: Firewall

## SSL/TLS Certificates for TURNS

### Using Let's Encrypt

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

### Certificate Renewal Hook

Create `/etc/letsencrypt/renewal-hooks/post/turnserver-restart.sh`:

```bash
#!/bin/bash
systemctl restart coturn
```

Make it executable:

```bash
sudo chmod +x /etc/letsencrypt/renewal-hooks/post/turnserver-restart.sh
```

## Testing the Integration

### 1. Start the signaling server

```bash
./start_secure_server.sh
```

### 2. Test the endpoint

```bash
# Login
curl -X POST https://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' \
  -k

# Get TURN credentials (use token from login)
curl -X GET https://localhost:8000/auth/turn-credentials \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -k
```

### 3. Use the example client

Open `examples/turn_credentials_example.html` in your browser and:
1. Enter your credentials
2. Click "Login"
3. Click "Get TURN Credentials"
4. Verify the credentials are generated correctly

### 4. Test in WebRTC application

```javascript
// Get credentials
const response = await fetch('https://localhost:8000/auth/turn-credentials', {
  headers: { 'Authorization': `Bearer ${token}` }
});
const turnCreds = await response.json();

// Use in RTCPeerConnection
const pc = new RTCPeerConnection({
  iceServers: [{
    urls: turnCreds.urls,
    username: turnCreds.username,
    credential: turnCreds.credential
  }]
});
```

## Monitoring and Troubleshooting

### Check coturn logs

```bash
sudo tail -f /var/log/turnserver.log
```

### Common issues

#### 1. "Authentication failed"
- Verify `TURNSERVER_SECRET` matches in both configs
- Check that credentials haven't expired (TTL)
- Ensure time is synchronized between servers (NTP)

#### 2. "Connection timeout"
- Check firewall rules
- Verify external-ip is correctly set
- Test connectivity with `telnet your-server.com 3478`

#### 3. "Certificate error"
- Ensure cert and pkey paths are correct
- Verify certificate isn't expired
- Check file permissions

#### 4. "Too many allocations"
- Increase `total-quota` in turnserver.conf
- Monitor resource usage
- Consider adding more TURN servers

### Performance monitoring

```bash
# Check active connections
sudo turnutils_uclient -T your-turn-server.com -P 3478

# Monitor system resources
htop
netstat -an | grep 3478
```

## Production Recommendations

1. **Use dedicated server**: Don't run TURN on the same server as the signaling server
2. **Enable monitoring**: Use Prometheus or similar tools
3. **Set resource limits**: Configure `max-bps` and `total-quota`
4. **Use TURNS**: Always provide TURNS (TLS) option for security
5. **Geographic distribution**: Deploy TURN servers in multiple regions
6. **Load balancing**: Use multiple TURN servers for redundancy
7. **Regular updates**: Keep coturn updated for security patches
8. **Monitor costs**: TURN servers can consume significant bandwidth

## Security Best Practices

1. Use strong shared secrets (32+ characters)
2. Enable TLS for TURNS
3. Set appropriate credential TTL (not too long)
4. Restrict relay ports with `max-port` and `min-port`
5. Enable fingerprint checking
6. Use `no-loopback-peers` to prevent localhost relay
7. Monitor for abuse
8. Implement rate limiting at network level
9. Keep logs for security auditing
10. Use `denied-peer-ip` to block specific ranges if needed

## Resources

- coturn GitHub: https://github.com/coturn/coturn
- coturn Wiki: https://github.com/coturn/coturn/wiki
- RFC 5766 (TURN): https://tools.ietf.org/html/rfc5766
- WebRTC samples: https://webrtc.github.io/samples/

## Support

For issues with:
- **coturn**: Check coturn GitHub issues
- **This integration**: Check this project's issues
- **WebRTC**: Check WebRTC documentation

## Example Complete Setup

Here's a complete example for a production server:

### /etc/turnserver.conf
```conf
realm=turn.example.com
server-name=turn.example.com
listening-port=3478
tls-listening-port=5349
listening-ip=0.0.0.0
relay-ip=203.0.113.10
external-ip=203.0.113.10
use-auth-secret
static-auth-secret=YOUR_SECRET_HERE
cert=/etc/letsencrypt/live/turn.example.com/cert.pem
pkey=/etc/letsencrypt/live/turn.example.com/privkey.pem
fingerprint
lt-cred-mech
no-loopback-peers
total-quota=100
max-bps=1000000
log-file=/var/log/turnserver.log
```

### .env (Signaling Server)
```bash
TURNSERVER_SECRET=YOUR_SECRET_HERE
TURNSERVER_URLS=["turn:turn.example.com:3478", "turns:turn.example.com:5349"]
TURNSERVER_TTL=86400
```

This setup provides both TURN (UDP/TCP) and TURNS (TLS) options for maximum compatibility.


