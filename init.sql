-- Database initialization script for Split App
-- This script sets up the initial database schema and constraints

-- Create extension for UUID generation (optional)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Ensure proper permissions
GRANT ALL PRIVILEGES ON DATABASE splitapp_db TO splitapp_user;

-- Create tables will be handled by SQLAlchemy migrations
-- This file serves as a placeholder for any custom SQL initialization