#!/bin/bash

# Configuration
DEFAULT_DOMAIN="c2.yourdomain.com"
DEFAULT_EMAIL="admin@yourdomain.com"

# Parse arguments
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        --domain)
        DOMAIN="$2"
        shift
        shift
        ;;
        --email)
        EMAIL="$2"
        shift
        shift
        ;;
        --password)
        ADMIN_PASSWORD="$2"
        shift
        shift
        ;;
        *)
        echo "Unknown option: $1"
        exit 1
        ;;
    esac
done

# Set defaults
DOMAIN=${DOMAIN:-$DEFAULT_DOMAIN}
EMAIL=${EMAIL:-$DEFAULT_EMAIL}

# Validate inputs
if [ -z "$ADMIN_PASSWORD" ]; then
    echo "Error: Admin password (--password) is required"
    exit 1
fi

# Deploy server
echo "Deploying C2 server..."
echo "- Domain: $DOMAIN"
echo "- Email: $EMAIL"

# Generate secrets
SECRET_KEY=$(openssl rand -base64 32)
JWT_SECRET=$(openssl rand -base64 32)

# Create docker-compose.yml
cat > docker-compose.yml << EOL
version: '3'

services:
  c2:
    build: .
    ports:
      - "80:80"
      - "443:443"
      - "8443:8443"
    environment:
      - SECRET_KEY=$SECRET_KEY
      - JWT_SECRET=$JWT_SECRET
      - ADMIN_PASSWORD=$ADMIN_PASSWORD
    volumes:
      - ./ssl:/etc/nginx/ssl
      - ./logs:/app/logs
    depends_on:
      - redis
      
  redis:
    image: redis:alpine
    volumes:
      - redis_data:/data

volumes:
  redis_data:
EOL

# Install SSL certificate
certbot certonly --standalone \
    -d $DOMAIN \
    -m $EMAIL \
    --agree-tos \
    --non-interactive

# Copy certificates
mkdir -p ssl
cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem ssl/server.crt
cp /etc/letsencrypt/live/$DOMAIN/privkey.pem ssl/server.key

# Start services
docker-compose up -d

if [ $? -eq 0 ]; then
    echo "Deployment successful!"
    echo "Admin interface: https://$DOMAIN:8443"
    echo "Admin credentials:"
    echo "- Username: admin"
    echo "- Password: $ADMIN_PASSWORD"
else
    echo "Deployment failed!"
    exit 1
fi
