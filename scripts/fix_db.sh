#!/bin/bash
echo "🛠️  Fixing PostgreSQL Permissions..."

# 1. Start Postgres if not running
brew services start postgresql

# 2. Create 'user' role (if missing)
# asyncpg often tries to connect as 'user' or current user
echo "Creating role 'user'..."
createuser -s user || echo "Role 'user' might already exist."

# 3. Create current user role (just in case)
CURRENT_USER=$(whoami)
echo "Creating role '$CURRENT_USER'..."
createuser -s $CURRENT_USER || echo "Role '$CURRENT_USER' might already exist."

# 4. Create database 'jarvis_db' (if missing)
echo "Creating database 'jarvis_db'..."
createdb jarvis_db || echo "Database 'jarvis_db' might already exist."

# 5. Enable Vector Extension
echo "Enabling pgvector..."
psql postgres -c "CREATE EXTENSION IF NOT EXISTS vector;"
psql jarvis_db -c "CREATE EXTENSION IF NOT EXISTS vector;"

echo "✅ Database Fix Complete. Try running 'python mitul.py' now."
