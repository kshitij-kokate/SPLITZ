# Deployment Guide - Expense Splitter API

## Production Deployment Summary

### ✅ Deployment Status
- **Platform**: Replit
- **Status**: Live and Running
- **Database**: PostgreSQL (Hosted)
- **Web Server**: Gunicorn with Flask
- **Environment**: Production-ready

### 🌐 Live URLs
```
Base API URL: https://[your-replit-domain].replit.app/api
Web Interface: https://[your-replit-domain].replit.app
Health Check: https://[your-replit-domain].replit.app/api/health
```

## 📊 Sample Data Verification

### Pre-populated Test Data
```
People: Shantanu, Sanket, Om
Expenses:
- Dinner: ₹600 (paid by Shantanu)
- Groceries: ₹450 (paid by Sanket) 
- Petrol: ₹300 (paid by Om)
- Movie Tickets: ₹500 (paid by Shantanu)
- Pizza: ₹280 (paid by Sanket)
```

### Expected Balances
```
Shantanu: +₹390 (should receive money)
Sanket: +₹20 (should receive money)
Om: -₹410 (owes money)
```

### Optimal Settlements
```
Om → Shantanu: ₹390
Om → Sanket: ₹20
Total Transactions: 2
```

## 🔧 Configuration Details

### Environment Variables
```
DATABASE_URL=postgresql://[auto-configured]
SESSION_SECRET=[auto-generated]
FLASK_ENV=production
PORT=5000
```

### Database Schema
```sql
-- Auto-created tables:
CREATE TABLE people (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE expenses (
    id SERIAL PRIMARY KEY,
    amount DECIMAL(10,2) NOT NULL,
    description VARCHAR(255) NOT NULL,
    paid_by_id INTEGER REFERENCES people(id),
    split_method VARCHAR(20) DEFAULT 'equal',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE expense_splits (
    id SERIAL PRIMARY KEY,
    expense_id INTEGER REFERENCES expenses(id),
    person_id INTEGER REFERENCES people(id),
    amount DECIMAL(10,2) NOT NULL,
    percentage DECIMAL(5,2),
    UNIQUE(expense_id, person_id)
);
```

## 🧪 Testing Verification

### Core API Tests
```bash
# Health Check
curl https://[your-domain].replit.app/api/health

# Get All Expenses
curl https://[your-domain].replit.app/api/expenses

# Get Balances
curl https://[your-domain].replit.app/api/balances

# Get Settlements
curl https://[your-domain].replit.app/api/settlements
```

### Validation Tests
```bash
# Test negative amount (should fail)
curl -X POST https://[your-domain].replit.app/api/expenses \
  -H "Content-Type: application/json" \
  -d '{"amount": -100, "description": "Test", "paid_by": "Test"}'

# Test empty description (should fail)
curl -X POST https://[your-domain].replit.app/api/expenses \
  -H "Content-Type: application/json" \
  -d '{"amount": 100, "description": "", "paid_by": "Test"}'
```

## 📋 Postman Collection Usage

### Import Instructions
1. Download `Expense_Splitter_API.postman_collection.json`
2. Open Postman → Import → Upload Files
3. Update `{{base_url}}` variable with your Replit URL
4. Run collection to verify all endpoints

### Collection Structure
```
📁 Expense Management (8 requests)
├── Add Dinner, Groceries, Petrol, Movie Tickets, Pizza
├── Custom Split Examples (Exact & Percentage)
├── List All Expenses
├── Update Expense
└── Delete Expense

📁 Settlements & People (4 requests)
├── Get All People
├── Get Current Balances
├── Get Settlement Summary
└── Health Check

📁 Edge Cases & Validation (9 requests)
├── Invalid Amounts, Descriptions, Missing Fields
├── Invalid Split Totals
├── Non-existent Resource Tests
└── Malformed JSON Tests
```

## 🚀 Performance Metrics

### Response Times (Expected)
```
GET /api/health: < 100ms
GET /api/expenses: < 300ms
POST /api/expenses: < 500ms
GET /api/balances: < 200ms
GET /api/settlements: < 150ms
```

### Scalability Features
- Database connection pooling
- Decimal precision for financial calculations
- Efficient settlement algorithm (O(n log n))
- Input validation prevents malformed requests
- Auto-scaling on Replit platform

## 🔒 Security Features

### Data Protection
- SQL injection prevention (parameterized queries)
- Input validation and sanitization
- Proper error handling (no sensitive data exposure)
- HTTPS encryption (Replit auto-configured)

### API Security
- Standardized error responses
- Request size limits
- Content-type validation
- Proper HTTP status codes

## 📈 Monitoring & Maintenance

### Health Monitoring
```bash
# Automated health check
curl -f https://[your-domain].replit.app/api/health || echo "API Down"

# Database connectivity test
curl https://[your-domain].replit.app/api/people
```

### Backup Strategy
- Replit handles automatic backups
- Database state preserved across restarts
- Code version control via Git

## 🛠 Troubleshooting

### Common Issues
```
Issue: API returns 500 errors
Solution: Check database connection, restart if needed

Issue: Balance calculations incorrect
Solution: Verify all expenses have proper splits

Issue: Validation not working
Solution: Check request Content-Type header

Issue: Settlement calculations empty
Solution: Ensure people have non-zero balances
```

### Debug Commands
```bash
# Check API status
curl -I https://[your-domain].replit.app/api/health

# Verify sample data
curl https://[your-domain].replit.app/api/people

# Test basic functionality
curl -X POST https://[your-domain].replit.app/api/expenses \
  -H "Content-Type: application/json" \
  -d '{"amount": 10, "description": "Test", "paid_by": "TestUser"}'
```

## 📋 Deployment Checklist

### ✅ Completed Items
- [x] Flask application deployed and running
- [x] PostgreSQL database configured and connected
- [x] All API endpoints functional and tested
- [x] Sample data populated (Shantanu, Sanket, Om)
- [x] Validation rules implemented and working
- [x] Settlement algorithm optimized and accurate
- [x] Error handling comprehensive
- [x] Web interface accessible and functional
- [x] Postman collection created and verified
- [x] Documentation complete and detailed
- [x] HTTPS enabled (Replit auto-configured)
- [x] Environment variables secured
- [x] Database schema created automatically
- [x] Response format standardized
- [x] All three split methods working (equal, exact, percentage)

### 🔍 Final Verification
Run the complete Postman collection to verify:
1. All 21 requests execute successfully
2. Validation catches all error cases
3. Sample data calculations are accurate
4. Settlement optimization works correctly
5. Error responses are properly formatted

The API is production-ready and fully deployed.