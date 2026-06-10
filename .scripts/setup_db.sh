#!/bin/bash
# .scripts/setup_db.sh
# Infrastructure script for managing the Postgres Docker container.

# 1. Check for .env
if [ ! -f .env ]; then
    echo "Error: .env file not found. Copying from .env.example..."
    cp .env.example .env
    echo "Please edit .env with your desired credentials, then run this script again."
    exit 1
fi

# 2. Check for Docker
if ! [ -x "$(command -v docker)" ]; then
  echo 'Error: docker is not installed.' >&2
  exit 1
fi

# 3. Spin up the database
echo "Starting PostgreSQL container..."
docker compose up -d

echo "------------------------------------------------"
echo "Database container is starting."
echo "To check logs:  docker compose logs -f db"
echo "To stop:        docker compose down"
echo "------------------------------------------------"
