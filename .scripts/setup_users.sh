#!/bin/bash
# .scripts/setup_users.sh
# Infrastructure script for provisioning service users.
# Run once with: sudo .scripts/setup_users.sh

# 1. Create OS Service User
echo "Creating elite_data_user..."
sudo useradd -r -s /usr/sbin/nologin elite_data_user || echo "User already exists."

# 2. Setup Data Directory Permissions
echo "Securing data directory..."
mkdir -p data/downloads data/schemas data/samples
sudo chown -R elite_data_user:elite_data_user data/
sudo chmod -R 750 data/

# 3. Create Postgres DB User (Mocked for now, requires postgres installed)
echo "Instruction for Postgres (Run as postgres user):"
echo "CREATE ROLE elite_db_role WITH LOGIN PASSWORD 'your_password_here';"
echo "GRANT ALL PRIVILEGES ON DATABASE elite_dangerous TO elite_db_role;"

echo "Setup Complete."
