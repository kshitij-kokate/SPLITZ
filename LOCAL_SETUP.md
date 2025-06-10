# Local Development Setup Guide

## Prerequisites

1. **Python 3.11+**
2. **PostgreSQL 12+** 
3. **Git**

## Quick Setup (Recommended)

### Option 1: Using Docker (Easiest)

```bash
# Clone the repository
git clone <your-repo-url>
cd split-app

# Start services with Docker Compose
docker-compose up -d

# The application will be available at http://localhost:5000
```

### Option 2: Manual Setup

#### Step 1: Install PostgreSQL

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

**macOS (with Homebrew):**
```bash
brew install postgresql
brew services start postgresql
```

**Windows:**
Download and install from https://www.postgresql.org/download/windows/

#### Step 2: Clone and Setup Application

```bash
# Clone the repository
git clone <your-repo-url>
cd split-app

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install flask flask-sqlalchemy psycopg2-binary gunicorn python-dotenv
```

#### Step 3: Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your database credentials
nano .env
```

Update the `.env` file with your PostgreSQL settings:
```env
DATABASE_URL=postgresql://splitapp_user:your_password@localhost:5432/splitapp_db
PGUSER=splitapp_user
PGPASSWORD=your_password
PGDATABASE=splitapp_db
```

#### Step 4: Setup Database

```bash
# Run the database setup script
python setup_database.py
```

When prompted, enter your PostgreSQL superuser password (usually the password for `postgres` user).

#### Step 5: Start Application

```bash
# Start the Flask development server
python main.py
```

The application will be available at `http://localhost:5000`

## Database Setup Details

### Manual Database Creation (Alternative)

If the setup script doesn't work, create the database manually:

```sql
-- Connect to PostgreSQL as superuser
sudo -u postgres psql

-- Create user and database
CREATE USER splitapp_user WITH PASSWORD 'your_password';
CREATE DATABASE splitapp_db OWNER splitapp_user;
GRANT ALL PRIVILEGES ON DATABASE splitapp_db TO splitapp_user;
\q
```

### Initialize Schema

```bash
# In your application directory
python -c "from app import app, db; app.app_context().push(); db.create_all()"

# Add sample data
python sample_data.py
```

## Verification

### Test Database Connection

```bash
# Test PostgreSQL connection
psql -h localhost -U splitapp_user -d splitapp_db -c "SELECT 1;"
```

### Test API Endpoints

```bash
# Health check
curl http://localhost:5000/api/health

# Get all people
curl http://localhost:5000/api/people

# Get balances
curl http://localhost:5000/api/balances
```

### Access Web Interface

Visit `http://localhost:5000` in your browser to use the web interface.

## Development Workflow

### Running in Development Mode

```bash
# Set environment variables
export FLASK_ENV=development
export FLASK_DEBUG=True

# Start with auto-reload
python main.py
```

### Database Migrations

```bash
# After modifying models, recreate tables
python -c "from app import app, db; app.app_context().push(); db.drop_all(); db.create_all()"

# Repopulate sample data
python sample_data.py
```

## Troubleshooting

### Common Issues

**1. PostgreSQL Connection Error**
```
psycopg2.OperationalError: could not connect to server
```
- Ensure PostgreSQL is running: `sudo systemctl status postgresql`
- Check port 5432 is open: `sudo netstat -plunt | grep 5432`
- Verify credentials in `.env` file

**2. Permission Denied**
```
psycopg2.errors.InsufficientPrivilege
```
- Ensure user has proper permissions: `GRANT ALL PRIVILEGES ON DATABASE splitapp_db TO splitapp_user;`

**3. Module Not Found**
```
ModuleNotFoundError: No module named 'flask'
```
- Activate virtual environment: `source venv/bin/activate`
- Install dependencies: `pip install -r requirements.txt`

**4. Database Does Not Exist**
```
psycopg2.OperationalError: database "splitapp_db" does not exist
```
- Run the setup script: `python setup_database.py`
- Or create manually using SQL commands above

### Reset Database

```bash
# Drop and recreate everything
python -c "
from app import app, db
app.app_context().push()
db.drop_all()
db.create_all()
"

# Repopulate sample data
python sample_data.py
```

### Check Logs

```bash
# View application logs
tail -f app.log

# View PostgreSQL logs (Ubuntu)
sudo tail -f /var/log/postgresql/postgresql-*.log
```

## Production Deployment

For production deployment, update your `.env` file:

```env
FLASK_ENV=production
FLASK_DEBUG=False
SESSION_SECRET=your-super-secure-random-key
DATABASE_URL=postgresql://user:password@prod-host:5432/splitapp_db
```

Use a production WSGI server:

```bash
gunicorn --bind 0.0.0.0:5000 --workers 4 main:app
```

## Project Structure

```
split-app/
├── .env                    # Environment variables
├── .env.example           # Environment template
├── app.py                 # Flask application setup
├── main.py                # Application entry point
├── models.py              # Database models
├── api_routes.py          # API endpoints
├── web_routes.py          # Web interface routes
├── settlement_calculator.py # Business logic
├── setup_database.py     # Database setup script
├── sample_data.py         # Sample data population
├── docker-compose.yml     # Docker setup
├── Dockerfile             # Docker image config
├── templates/             # HTML templates
├── static/                # CSS, JS, images
└── README.md              # Project documentation
```