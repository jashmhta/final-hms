#!/bin/bash
set -e

# Wait for database to be ready
echo "Waiting for database to be ready..."
until python -c "import django; django.setup(); from django.db import connection; cursor = connection.cursor(); cursor.execute('SELECT 1')" 2>/dev/null; do
    echo "Database is unavailable - sleeping"
    sleep 2
done

echo "Database is ready!"

# Run database migrations
echo "Running database migrations..."
python manage.py migrate --noinput

# Create superuser if needed
if [ "$DJANGO_CREATE_SUPERUSER" = "true" ]; then
    echo "Creating superuser..."
    python manage.py createsuperuser --noinput || true
fi

# Load initial data if needed
if [ "$DJANGO_LOAD_INITIAL_DATA" = "true" ]; then
    echo "Loading initial data..."
    python manage.py loaddata initial_data || true
fi

# Generate SSH keys for secure communication
if [ ! -f /app/keys/app_rsa ]; then
    echo "Generating SSH keys..."
    mkdir -p /app/keys
    ssh-keygen -t rsa -b 4096 -f /app/keys/app_rsa -N ""
    chmod 600 /app/keys/app_rsa*
fi

# Set proper permissions
chown -R appuser:appuser /app

# Start the application
echo "Starting HMS application..."
exec "$@"