#!/usr/bin/env python3
"""
Database setup script for Split App
Creates database, user, and initializes schema
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
DB_NAME = os.getenv('PGDATABASE', 'splitapp_db')
DB_USER = os.getenv('PGUSER', 'splitapp_user')
DB_PASSWORD = os.getenv('PGPASSWORD', 'splitapp_password')
DB_HOST = os.getenv('PGHOST', 'localhost')
DB_PORT = os.getenv('PGPORT', '5432')

def create_database_and_user():
    """Create database and user if they don't exist"""
    try:
        # Connect to PostgreSQL as superuser
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user='postgres',  # Default superuser
            password=input("Enter PostgreSQL superuser password: ")
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Create user if not exists
        try:
            cursor.execute(f"""
                CREATE USER {DB_USER} WITH PASSWORD '{DB_PASSWORD}';
            """)
            print(f"✓ Created user: {DB_USER}")
        except psycopg2.errors.DuplicateObject:
            print(f"✓ User {DB_USER} already exists")
        
        # Create database if not exists
        try:
            cursor.execute(f"""
                CREATE DATABASE {DB_NAME} OWNER {DB_USER};
            """)
            print(f"✓ Created database: {DB_NAME}")
        except psycopg2.errors.DuplicateDatabase:
            print(f"✓ Database {DB_NAME} already exists")
        
        # Grant privileges
        cursor.execute(f"""
            GRANT ALL PRIVILEGES ON DATABASE {DB_NAME} TO {DB_USER};
        """)
        print(f"✓ Granted privileges to {DB_USER}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"✗ Error creating database/user: {e}")
        return False
    
    return True

def test_connection():
    """Test connection to the application database"""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cursor = conn.cursor()
        cursor.execute("SELECT 1;")
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if result[0] == 1:
            print("✓ Database connection successful")
            return True
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False

def initialize_schema():
    """Initialize database schema using Flask app"""
    try:
        # Import app to trigger table creation
        from app import app, db
        
        with app.app_context():
            # Create all tables
            db.create_all()
            print("✓ Database schema initialized")
            
            # Add sample data if tables are empty
            from models import Person, Expense
            if Person.query.count() == 0:
                print("Adding sample data...")
                from sample_data import populate_sample_data
                populate_sample_data()
                print("✓ Sample data added")
            else:
                print("✓ Sample data already exists")
                
        return True
    except Exception as e:
        print(f"✗ Error initializing schema: {e}")
        return False

def main():
    """Main setup function"""
    print("Split App - Database Setup")
    print("=" * 30)
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("✗ .env file not found. Please copy .env.example to .env and configure it.")
        sys.exit(1)
    
    print(f"Setting up database: {DB_NAME}")
    print(f"User: {DB_USER}")
    print(f"Host: {DB_HOST}:{DB_PORT}")
    print()
    
    # Step 1: Create database and user
    print("Step 1: Creating database and user...")
    if not create_database_and_user():
        print("Failed to create database/user. Exiting.")
        sys.exit(1)
    
    # Step 2: Test connection
    print("\nStep 2: Testing connection...")
    if not test_connection():
        print("Failed to connect to database. Please check your configuration.")
        sys.exit(1)
    
    # Step 3: Initialize schema
    print("\nStep 3: Initializing schema...")
    if not initialize_schema():
        print("Failed to initialize schema. Please check the error above.")
        sys.exit(1)
    
    print("\n" + "=" * 30)
    print("✓ Database setup completed successfully!")
    print(f"✓ Database URL: postgresql://{DB_USER}:***@{DB_HOST}:{DB_PORT}/{DB_NAME}")
    print("\nYou can now run the application with:")
    print("python main.py")

if __name__ == "__main__":
    main()