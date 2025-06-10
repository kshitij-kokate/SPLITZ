#!/usr/bin/env python3
"""
Local development runner for Split App
Loads environment variables and starts the Flask development server
"""

import os
import sys
from dotenv import load_dotenv

def main():
    """Load environment and start the application"""
    
    # Load environment variables from .env file
    if os.path.exists('.env'):
        load_dotenv('.env')
        print("Loaded environment variables from .env")
    else:
        print("Warning: .env file not found. Using system environment variables.")
        print("Copy .env.example to .env and configure your database settings.")
    
    # Import and run the Flask app
    try:
        from app import app
        
        # Configuration for local development
        app.config['DEBUG'] = True
        app.config['ENV'] = 'development'
        
        host = os.getenv('HOST', '0.0.0.0')
        port = int(os.getenv('PORT', 5000))
        
        print(f"Starting Split App on http://{host}:{port}")
        print("Press Ctrl+C to stop the server")
        
        app.run(host=host, port=port, debug=True)
        
    except ImportError as e:
        print(f"Error importing application: {e}")
        print("Make sure all dependencies are installed:")
        print("pip install flask flask-sqlalchemy psycopg2-binary python-dotenv")
        sys.exit(1)
    except Exception as e:
        print(f"Error starting application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()