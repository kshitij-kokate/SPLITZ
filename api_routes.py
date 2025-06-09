from flask import Blueprint, request, jsonify
from app import db
from models import Person, Expense, ExpenseSplit, SplitMethod
from settlement_calculator import SettlementCalculator
from decimal import Decimal, InvalidOperation
import logging

api = Blueprint('api', __name__)

def create_response(success=True, data=None, message="", status_code=200):
    """Create standardized API response"""
    response = {
        'success': success,
        'data': data,
        'message': message
    }
    return jsonify(response), status_code

def validate_expense_data(data):
    """Validate expense data"""
    errors = []
    
    if not data.get('amount'):
        errors.append("Amount is required")
    else:
        try:
            amount = Decimal(str(data['amount']))
            if amount <= 0:
                errors.append("Amount must be greater than 0")
        except (InvalidOperation, ValueError):
            errors.append("Amount must be a valid number")
    
    if not data.get('description') or not data['description'].strip():
        errors.append("Description is required and cannot be empty")
    
    if not data.get('paid_by') or not data['paid_by'].strip():
        errors.append("paid_by is required and cannot be empty")
    
    return errors

@api.route('/expenses', methods=['POST'])
def create_expense():
    """Create a new expense"""
    try:
        data = request.get_json()
        if not data:
            return create_response(False, None, "Request body is required", 400)
        
        # Validate input
        errors = validate_expense_data(data)
        if errors:
            return create_response(False, None, "; ".join(errors), 400)
        
        # Get or create the person who paid
        paid_by_name = data['paid_by'].strip()
        person = Person.query.filter_by(name=paid_by_name).first()
        if not person:
            person = Person(name=paid_by_name)
            db.session.add(person)
            db.session.flush()  # Get the ID
        
        # Create the expense
        expense = Expense(
            amount=Decimal(str(data['amount'])),
            description=data['description'].strip(),
            paid_by_id=person.id,
            split_method=SplitMethod.EQUAL
        )
        db.session.add(expense)
        db.session.flush()  # Get the expense ID
        
        # Get all people for equal split (or use participants if provided)
        participants = data.get('participants', [paid_by_name])
        if paid_by_name not in participants:
            participants.append(paid_by_name)
        
        # Create equal splits
        SettlementCalculator.create_equal_splits(expense.id, participants)
        
        db.session.commit()
        
        return create_response(True, expense.to_dict(), "Expense created successfully", 201)
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error creating expense: {str(e)}")
        return create_response(False, None, f"Internal server error: {str(e)}", 500)

@api.route('/expenses', methods=['GET'])
def get_expenses():
    """Get all expenses"""
    try:
        expenses = Expense.query.order_by(Expense.created_at.desc()).all()
        expenses_data = [expense.to_dict() for expense in expenses]
        
        return create_response(True, expenses_data, "Expenses retrieved successfully")
        
    except Exception as e:
        logging.error(f"Error retrieving expenses: {str(e)}")
        return create_response(False, None, f"Internal server error: {str(e)}", 500)

@api.route('/expenses/<int:expense_id>', methods=['PUT'])
def update_expense(expense_id):
    """Update an existing expense"""
    try:
        expense = Expense.query.get(expense_id)
        if not expense:
            return create_response(False, None, "Expense not found", 404)
        
        data = request.get_json()
        if not data:
            return create_response(False, None, "Request body is required", 400)
        
        # Validate input if provided
        if 'amount' in data or 'description' in data or 'paid_by' in data:
            # Create a complete data dict for validation
            validation_data = {
                'amount': data.get('amount', expense.amount),
                'description': data.get('description', expense.description),
                'paid_by': data.get('paid_by', expense.payer.name)
            }
            
            errors = validate_expense_data(validation_data)
            if errors:
                return create_response(False, None, "; ".join(errors), 400)
        
        # Update fields if provided
        if 'amount' in data:
            expense.amount = Decimal(str(data['amount']))
        
        if 'description' in data:
            expense.description = data['description'].strip()
        
        if 'paid_by' in data:
            paid_by_name = data['paid_by'].strip()
            person = Person.query.filter_by(name=paid_by_name).first()
            if not person:
                person = Person(name=paid_by_name)
                db.session.add(person)
                db.session.flush()
            expense.paid_by_id = person.id
        
        # If amount changed or participants changed, recreate splits
        if 'amount' in data or 'participants' in data:
            participants = data.get('participants', [expense.payer.name])
            if expense.payer.name not in participants:
                participants.append(expense.payer.name)
            
            SettlementCalculator.create_equal_splits(expense.id, participants)
        
        db.session.commit()
        
        return create_response(True, expense.to_dict(), "Expense updated successfully")
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error updating expense: {str(e)}")
        return create_response(False, None, f"Internal server error: {str(e)}", 500)

@api.route('/expenses/<int:expense_id>', methods=['DELETE'])
def delete_expense(expense_id):
    """Delete an expense"""
    try:
        expense = Expense.query.get(expense_id)
        if not expense:
            return create_response(False, None, "Expense not found", 404)
        
        db.session.delete(expense)
        db.session.commit()
        
        return create_response(True, None, "Expense deleted successfully")
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error deleting expense: {str(e)}")
        return create_response(False, None, f"Internal server error: {str(e)}", 500)

@api.route('/people', methods=['GET'])
def get_people():
    """Get all people"""
    try:
        people = Person.query.order_by(Person.name).all()
        people_data = [person.to_dict() for person in people]
        
        return create_response(True, people_data, "People retrieved successfully")
        
    except Exception as e:
        logging.error(f"Error retrieving people: {str(e)}")
        return create_response(False, None, f"Internal server error: {str(e)}", 500)

@api.route('/balances', methods=['GET'])
def get_balances():
    """Get current balances for all people"""
    try:
        balances = SettlementCalculator.calculate_balances()
        balances_list = list(balances.values())
        
        return create_response(True, balances_list, "Balances calculated successfully")
        
    except Exception as e:
        logging.error(f"Error calculating balances: {str(e)}")
        return create_response(False, None, f"Internal server error: {str(e)}", 500)

@api.route('/settlements', methods=['GET'])
def get_settlements():
    """Get optimal settlements to balance all debts"""
    try:
        settlements = SettlementCalculator.calculate_settlements()
        
        return create_response(True, settlements, "Settlements calculated successfully")
        
    except Exception as e:
        logging.error(f"Error calculating settlements: {str(e)}")
        return create_response(False, None, f"Internal server error: {str(e)}", 500)

# Health check endpoint
@api.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return create_response(True, {"status": "healthy"}, "Service is running")
