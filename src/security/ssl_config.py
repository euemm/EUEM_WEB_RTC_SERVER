"""
SSL/TLS Configuration
Handles SSL certificates and HTTPS/WSS configuration
"""

import os
import ssl
import ipaddress
from pathlib import Path
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class SSLManager:
    """Manages SSL certificates for development and production"""
    
    def __init__(self, cert_dir: str = "ssl"):
        self.cert_dir = Path(cert_dir)
        self.cert_dir.mkdir(exist_ok=True)
        
        self.cert_file = self.cert_dir / "server.crt"
        self.key_file = self.cert_dir / "server.key"
    
    def generate_self_signed_cert(self, hostname: str = "localhost"):
        """Generate self-signed certificate for development"""
        if self.cert_file.exists() and self.key_file.exists():
            logger.info("SSL certificates already exist")
            return
        
        logger.info(f"Generating self-signed SSL certificate for {hostname}")
        
        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        
        # Create certificate
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Development"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "Local"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "WebRTC Signaling Server"),
            x509.NameAttribute(NameOID.COMMON_NAME, hostname),
        ])
        
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.utcnow()
        ).not_valid_after(
            datetime.utcnow() + timedelta(days=365)
        ).add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName(hostname),
                x509.DNSName("127.0.0.1"),
                x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
            ]),
            critical=False,
        ).sign(private_key, hashes.SHA256())
        
        # Write certificate to file
        with open(self.cert_file, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        
        # Write private key to file
        with open(self.key_file, "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
        
        logger.info(f"SSL certificate generated: {self.cert_file}")
        logger.info(f"SSL private key generated: {self.key_file}")
    
    def get_ssl_context(self) -> ssl.SSLContext:
        """Get SSL context for HTTPS/WSS"""
        if not self.cert_file.exists() or not self.key_file.exists():
            logger.warning("SSL certificates not found, generating self-signed certificate")
            self.generate_self_signed_cert()
        
        # Create SSL context
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(self.cert_file, self.key_file)
        
        # Security settings
        context.set_ciphers('ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS')
        context.options |= ssl.OP_NO_SSLv2
        context.options |= ssl.OP_NO_SSLv3
        context.options |= ssl.OP_NO_TLSv1
        context.options |= ssl.OP_NO_TLSv1_1
        
        return context
    
    def verify_production_cert(self) -> bool:
        """Verify production SSL certificates"""
        if not self.cert_file.exists() or not self.key_file.exists():
            return False
        
        try:
            with open(self.cert_file, 'rb') as f:
                cert_data = f.read()
            
            cert = x509.load_pem_x509_certificate(cert_data)
            
            # Check if certificate is self-signed (development)
            if cert.issuer == cert.subject:
                logger.warning("Using self-signed certificate - not suitable for production")
                return False
            
            # Check expiration
            now = datetime.utcnow()
            if cert.not_valid_after < now:
                logger.error("SSL certificate has expired")
                return False
            
            logger.info("Production SSL certificate is valid")
            return True
            
        except Exception as e:
            logger.error(f"Error verifying SSL certificate: {e}")
            return False

# Global SSL manager instance
ssl_manager = SSLManager()

def get_ssl_context():
    """Get SSL context for the server"""
    return ssl_manager.get_ssl_context()

def verify_ssl_setup():
    """Verify SSL setup for production"""
    return ssl_manager.verify_production_cert()
