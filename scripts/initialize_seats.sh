#!/bin/sh
set -e

echo "⏳ Waiting for PostgreSQL to be ready..."
until PGPASSWORD=$POSTGRES_PASSWORD psql -h "$DB_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT 1;" > /dev/null 2>&1; do
    echo "🔄 Waiting for database..."
    sleep 2
done

echo "✅ Database is ready! Running seat initialization..."
python initialize_seats.py
echo "🎉 Seat initialization complete!"
