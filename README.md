# Split App - Production-Ready Expense Splitter API

A comprehensive Flask-based RESTful API for expense splitting and settlement calculations, similar to Splitwise or Google Pay's bill-splitting feature.

## 🚀 Live Deployment

**API Base URL:** `https://[your-replit-url].replit.app/api`
**Web Interface:** `https://[your-replit-url].replit.app`

## 📋 Features

### Core Functionality
- **Expense Management**: Create, read, update, delete expenses
- **Multiple Split Methods**: Equal, exact amounts, percentage-based splits
- **Automatic Settlement Calculation**: Minimizes transaction count using greedy algorithm
- **People Management**: Auto-creation of users when mentioned in expenses
- **Real-time Balance Tracking**: Calculate who owes whom

### Advanced Features
- **Comprehensive Validation**: Input validation with detailed error messages
- **Flexible Split Options**: Support for complex splitting scenarios
- **Web Interface**: User-friendly dashboard with Bootstrap dark theme
- **PostgreSQL Database**: Production-ready data persistence
- **Error Handling**: Robust error responses with proper HTTP status codes

## 🛠 API Endpoints

### Expense Management
```
POST   /api/expenses       - Create new expense
GET    /api/expenses       - List all expenses
PUT    /api/expenses/:id   - Update expense
DELETE /api/expenses/:id   - Delete expense
```

### Settlement & People
```
GET    /api/people         - List all people
GET    /api/balances       - Get current balances
GET    /api/settlements    - Get optimal settlement transactions
GET    /api/health         - Health check
```

## 📊 API Response Format

All API responses follow this standardized format:

```json
{
  "success": true/false,
  "data": {...},
  "message": "Status message"
}
```

## 💡 Split Methods

### 1. Equal Split (Default)
Divides expense equally among selected participants.

```json
{
  "amount": 600,
  "description": "Dinner",
  "paid_by": "Shantanu",
  "split_method": "equal",
  "participants": ["Shantanu", "Sanket", "Om"]
}
```

### 2. Exact Amounts
Specify exact dollar amounts for each person.

```json
{
  "amount": 100,
  "description": "Shopping",
  "paid_by": "Shantanu",
  "split_method": "exact",
  "splits": [
    {"person": "Shantanu", "amount": 40.00},
    {"person": "Sanket", "amount": 35.00},
    {"person": "Om", "amount": 25.00}
  ]
}
```

### 3. Percentage Split
Specify percentages that must total 100%.

```json
{
  "amount": 100,
  "description": "Project costs",
  "paid_by": "Shantanu",
  "split_method": "percentage",
  "splits": [
    {"person": "Shantanu", "percentage": 50.0},
    {"person": "Sanket", "percentage": 30.0},
    {"person": "Om", "percentage": 20.0}
  ]
}
```

## 🗄 Database Schema

### People Table
- `id` (Primary Key)
- `name` (Unique, Not Null)
- `created_at` (Timestamp)

### Expenses Table
- `id` (Primary Key)
- `amount` (Decimal, Not Null)
- `description` (String, Not Null)
- `paid_by_id` (Foreign Key to People)
- `split_method` (Enum: equal, exact, percentage)
- `created_at`, `updated_at` (Timestamps)

### Expense Splits Table
- `id` (Primary Key)
- `expense_id` (Foreign Key to Expenses)
- `person_id` (Foreign Key to People)
- `amount` (Decimal, Not Null)
- `percentage` (Decimal, Nullable)

## 🏗 Local Development Setup

### Prerequisites
- Python 3.11+
- PostgreSQL
- Flask and dependencies (see requirements)

### Installation
1. Clone the repository
2. Install dependencies:
   ```bash
   pip install flask flask-sqlalchemy psycopg2-binary gunicorn
   ```
3. Set environment variables:
   ```bash
   export DATABASE_URL="postgresql://user:password@localhost/splitapp"
   export SESSION_SECRET="your-secret-key"
   ```
4. Run the application:
   ```bash
   python main.py
   ```

### Database Setup
The application automatically creates tables on startup. For production:
1. Create PostgreSQL database
2. Set DATABASE_URL environment variable
3. Run the application to initialize schema

## 🧪 Testing

### Sample Test Data
The application includes pre-populated sample data:
- **People**: Shantanu, Sanket, Om
- **Expenses**: Dinner (₹600), Groceries (₹450), Petrol (₹300), Movie Tickets (₹500), Pizza (₹280)

### Validation Testing
- Negative amounts → 400 Bad Request
- Empty descriptions → 400 Bad Request
- Missing required fields → 400 Bad Request
- Invalid split totals → 400 Bad Request
- Non-existent resources → 404 Not Found

## 💻 Settlement Algorithm

The settlement calculator uses a greedy algorithm to minimize transaction count:

1. **Calculate Balances**: `total_paid - fair_share` for each person
2. **Identify Creditors/Debtors**: Positive balance = owed money, Negative = owes money
3. **Optimize Transactions**: Match largest creditor with largest debtor
4. **Minimize Count**: Continue until all balances are settled

### Example Settlement
```json
[
  {"from": "Om", "to": "Shantanu", "amount": 410.00},
  {"from": "Sanket", "to": "Shantanu", "amount": 20.00}
]
```

## 🔧 Configuration

### Environment Variables
- `DATABASE_URL`: PostgreSQL connection string
- `SESSION_SECRET`: Flask session secret key
- `FLASK_ENV`: Environment (development/production)

### Production Deployment
1. Set all environment variables
2. Use production-grade WSGI server (Gunicorn)
3. Configure reverse proxy (Nginx)
4. Enable SSL/TLS certificates

## 📚 API Documentation

### Error Codes
- `200` - Success
- `201` - Created
- `400` - Bad Request (validation errors)
- `404` - Not Found
- `500` - Internal Server Error

### Common Error Responses
```json
{
  "success": false,
  "data": null,
  "message": "Amount must be greater than 0"
}
```

## 🎯 Business Logic

### Balance Calculation
```
Balance = Total Paid - Fair Share
Positive Balance = Person is owed money
Negative Balance = Person owes money
Zero Balance = Person is settled
```

### Split Validation
- **Equal**: Participants must be selected
- **Exact**: Split amounts must equal expense total
- **Percentage**: Percentages must sum to 100%

## 🚀 Deployment Notes

### Replit Deployment
- Application runs on port 5000
- Database hosted on Replit PostgreSQL
- Environment variables configured automatically
- Auto-scaling and health monitoring included

### Performance Considerations
- Database connection pooling enabled
- Decimal precision for financial calculations
- Efficient settlement algorithm (O(n log n))
- Input validation to prevent malformed requests

## 📞 Support

For issues or questions:
1. Check API response messages for detailed error information
2. Verify request format matches documentation
3. Ensure all required fields are provided
4. Check that split totals are valid

## 🔄 Version History

**v1.0.0** - Production Release
- Complete expense management
- Three split methods
- Settlement optimization
- Web interface
- Comprehensive validation
- Production deployment