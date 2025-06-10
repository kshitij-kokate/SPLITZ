"""
Sample data population script for Split App
Populates database with sample people and expenses for testing
"""

from app import db
from models import Person, Expense, SplitMethod
from settlement_calculator import SettlementCalculator

def populate_sample_data():
    """Populate database with sample data for testing"""
    
    # Sample people
    people_data = [
        "Shantanu",
        "Sanket", 
        "Om"
    ]
    
    # Create people
    people = {}
    for name in people_data:
        person = Person.query.filter_by(name=name).first()
        if not person:
            person = Person(name=name)
            db.session.add(person)
            db.session.flush()
        people[name] = person
    
    # Sample expenses
    expenses_data = [
        {
            "amount": 600,
            "description": "Dinner",
            "paid_by": "Shantanu",
            "participants": ["Shantanu", "Sanket", "Om"]
        },
        {
            "amount": 450,
            "description": "Groceries", 
            "paid_by": "Sanket",
            "participants": ["Shantanu", "Sanket", "Om"]
        },
        {
            "amount": 300,
            "description": "Petrol",
            "paid_by": "Om", 
            "participants": ["Shantanu", "Sanket", "Om"]
        },
        {
            "amount": 500,
            "description": "Movie Tickets",
            "paid_by": "Shantanu",
            "participants": ["Shantanu", "Sanket", "Om"]
        },
        {
            "amount": 280,
            "description": "Pizza",
            "paid_by": "Sanket",
            "participants": ["Shantanu", "Sanket", "Om"]
        }
    ]
    
    # Create expenses
    for expense_data in expenses_data:
        # Check if expense already exists
        existing = Expense.query.filter_by(
            description=expense_data["description"],
            amount=expense_data["amount"]
        ).first()
        
        if not existing:
            payer = people[expense_data["paid_by"]]
            
            expense = Expense(
                amount=expense_data["amount"],
                description=expense_data["description"],
                paid_by_id=payer.id,
                split_method=SplitMethod.EQUAL
            )
            db.session.add(expense)
            db.session.flush()
            
            # Create equal splits
            SettlementCalculator.create_equal_splits(
                expense.id, 
                expense_data["participants"]
            )
    
    db.session.commit()
    print("Sample data populated successfully!")

if __name__ == "__main__":
    from app import app
    with app.app_context():
        populate_sample_data()