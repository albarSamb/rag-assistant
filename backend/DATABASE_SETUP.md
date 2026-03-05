# Database Setup Guide

## Prerequisites

### Install PostgreSQL 16

**Windows:**
1. Download from: https://www.postgresql.org/download/windows/
2. Run installer
3. Default port: 5432
4. Remember your postgres password

### Create Database

```powershell
# Connect as postgres user
psql -U postgres

# In psql console:
CREATE DATABASE docubot;
CREATE USER docubot WITH PASSWORD 'docubot';
GRANT ALL PRIVILEGES ON DATABASE docubot TO docubot;
\q
```

## Configuration

1. Copy `.env.example` to `.env`:
```powershell
cp .env.example .env
```

2. Update DATABASE_URL in `.env` if needed:
```
DATABASE_URL=postgresql+asyncpg://docubot:docubot@localhost:5432/docubot
```

## Migrations

### Create Initial Migration

```powershell
# Generate migration from models
alembic revision --autogenerate -m "Initial migration"
```

### Apply Migrations

```powershell
# Apply all pending migrations
alembic upgrade head
```

### Check Migration Status

```powershell
# Show current migration version
alembic current

# Show migration history
alembic history
```

### Rollback

```powershell
# Rollback one migration
alembic downgrade -1

# Rollback to specific version
alembic downgrade <revision>

# Rollback all
alembic downgrade base
```

## Quick Start (without PostgreSQL for now)

If you don't have PostgreSQL installed yet, you can use SQLite for testing:

1. Update `.env`:
```
DATABASE_URL=sqlite+aiosqlite:///./docubot.db
```

2. Install aiosqlite:
```powershell
pip install aiosqlite
```

3. Run migrations:
```powershell
alembic upgrade head
```

## Verify Database

```powershell
# Connect to database
psql -U docubot -d docubot

# List tables
\dt

# Expected tables:
# - users
# - documents  
# - conversations
# - messages
# - alembic_version

# Exit
\q
```

## Troubleshooting

### Connection refused
- Check PostgreSQL is running: `pg_ctl status`
- Start PostgreSQL: `pg_ctl start`

### Authentication failed
- Verify username/password in DATABASE_URL matches PostgreSQL user

### Cannot find psql command
- Add PostgreSQL bin folder to PATH:
  - Default: `C:\Program Files\PostgreSQL\16\bin`
