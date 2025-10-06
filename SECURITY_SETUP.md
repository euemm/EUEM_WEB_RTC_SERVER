# Security Setup Guide

## 🔐 Sensitive Files Protection

This guide explains how to properly set up the WebRTC Signaling Server without exposing sensitive information to version control.

## 📁 Files Protected by .gitignore

The following sensitive files are automatically ignored by git:

### SSL/TLS Certificates
- `ssl/` directory and all contents
- `*.crt`, `*.key`, `*.pem`, `*.p12`, `*.pfx` files

### User Data
- `users.csv` - Contains user credentials and password hashes
- `user_data/` directory
- `auth_data/` directory

### Configuration Files
- `.env` - Environment variables with secrets
- `config.ini` - Configuration with sensitive data
- `secrets.json` - JSON configuration with secrets

### Logs and Runtime Files
- `server.log`, `access.log`, `error.log`
- `*.db`, `*.sqlite`, `*.sqlite3` database files

## 🚀 Initial Setup

### 1. Environment Configuration
```bash
# Copy the example environment file
cp env.example .env

# Edit .env with your settings
nano .env
```

**Important:** Change these values in production:
- `SECRET_KEY` - Use a strong 256-bit secret
- `JWT_SECRET_KEY` - Use a different strong secret for JWT signing
- `CORS_ORIGINS` - Limit to your actual domains
- `REQUIRE_HTTPS=true` - Enable HTTPS enforcement

### 2. SSL Certificates (for HTTPS/WSS)

The server will automatically generate self-signed certificates for development:

```bash
# Certificates are generated automatically on first run
./start_secure_server.sh
```

For production, replace the auto-generated certificates in `ssl/` with real certificates from a trusted CA.

### 3. User Management

Default users are created automatically in `users.csv`. For production:

1. **Change default passwords** immediately
2. **Use strong passwords** (12+ characters)
3. **Remove test users** if not needed
4. **Add your own users** as needed

Default users (change these passwords!):
- `admin` / `admin123`
- `user1` / `password123`
- `user2` / `password123`

## 🔒 Security Best Practices

### Development
- Use `REQUIRE_HTTPS=false` for local development
- Self-signed certificates are acceptable for local testing
- Default passwords are acceptable for development only

### Production
- **ALWAYS** use `REQUIRE_HTTPS=true`
- **ALWAYS** use real SSL certificates from a trusted CA
- **ALWAYS** change all default passwords
- **ALWAYS** use strong, unique secrets in `.env`
- **ALWAYS** limit `CORS_ORIGINS` to your actual domains
- **ALWAYS** use a secure password hashing method (bcrypt is enabled)

### File Permissions
```bash
# Secure sensitive files
chmod 600 .env
chmod 600 ssl/server.key
chmod 644 ssl/server.crt
chmod 644 users.csv
```

## 🚨 Security Checklist

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

## 📝 Example Production .env

```bash
HOST=0.0.0.0
PORT=8000
DEBUG=false
REQUIRE_HTTPS=true
CORS_ORIGINS=["https://yourdomain.com", "https://app.yourdomain.com"]
SECRET_KEY=your-256-bit-secret-key-here
JWT_SECRET_KEY=your-different-jwt-secret-key-here
LOG_LEVEL=INFO
RATE_LIMIT_PER_MINUTE=60
```

## 🔍 Monitoring

Monitor these files for security:
- `server.log` - Check for authentication failures
- `access.log` - Monitor for suspicious requests
- `users.csv` - Regular user access reviews

## ⚠️ Important Notes

1. **Never commit** `.env`, `users.csv`, or `ssl/` files to git
2. **Never share** private keys or passwords
3. **Regularly rotate** secrets and passwords
4. **Monitor logs** for security issues
5. **Keep dependencies** updated for security patches
