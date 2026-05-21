#!/bin/sh

# Exit immediately if a command exits with a non-zero status
set -e

# Wait for the database to be ready
if [ "$DATABASE" = "postgres" ]
then
    echo "Waiting for postgres..."

    # Robust check using a small python script that tries to actual connect
    while ! python <<EOF
import sys
import psycopg2
try:
    conn = psycopg2.connect(
        dbname="$DB_NAME",
        user="$DB_USER",
        password="$DB_PASSWORD",
        host="$DB_HOST",
        port="$DB_PORT"
    )
except psycopg2.OperationalError:
    sys.exit(1)
sys.exit(0)
EOF
    do
      echo "Postgres is unavailable - sleeping"
      sleep 1
    done

    echo "PostgreSQL started"
fi

# Apply migrations (Only on one container to prevent race conditions)
if [ "$RUN_MIGRATIONS" = "true" ]
then
    echo "Making migrations..."
    python manage.py makemigrations --noinput

    echo "Applying migrations..."
    python manage.py migrate --noinput

    echo "Collecting static files..."
    python manage.py collectstatic --noinput

    # Create superuser from environment variables
    echo "Ensuring superuser exists..."
    python manage.py create_admin
fi

# Execute the main container process
exec "$@"
