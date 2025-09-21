#!/bin/bash
set -e

# Create nginx directories
mkdir -p /var/log/nginx /var/lib/nginx/cache /var/lib/nginx/tmp
chown -R nginx:nginx /var/log/nginx /var/lib/nginx/cache /var/lib/nginx/tmp

# Generate DH parameters for better security
if [ ! -f /etc/nginx/dhparam.pem ]; then
    echo "Generating DH parameters..."
    openssl dhparam -out /etc/nginx/dhparam.pem 2048
fi

# Test nginx configuration
echo "Testing nginx configuration..."
nginx -t

# Start nginx
echo "Starting nginx..."
exec nginx -g "daemon off;"