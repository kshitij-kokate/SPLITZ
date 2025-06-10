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
    
    # Validate split method if provided
    split_method = data.get('split_method', 'equal')
    if split_method not in ['equal', 'exact', 'percentage']:
        errors.append("split_method must be one of: equal, exact, percentage")
    
    # Validate splits array for custom split methods
    if split_method in ['exact', 'percentage'] and 'splits' in data:
        splits = data.get('splits', [])
        if not splits:
            errors.append(f"splits array is required for {split_method} split method")
        else:
            errors.extend(validate_splits(splits, split_method, data.get('amount')))
    
    return errors

def validate_splits(splits, split_method, total_amount):
    """Validate splits array based on split method"""
    errors = []
    
    if not isinstance(splits, list):
        errors.append("splits must be an array")
        return errors
    
    if len(splits) == 0:
        errors.append("splits array cannot be empty")
        return errors
    
    # Check for duplicate people
    people_names = []
    for split in splits:
        if not isinstance(split, dict):
            errors.append("Each split must be an object")
            continue
            
        person = split.get('person', '').strip()
        if not person:
            errors.append("Each split must have a person name")
            continue
            
        if person in people_names:
            errors.append(f"Duplicate person '{person}' in splits")
        else:
            people_names.append(person)
    
    if split_method == 'exact':
        # Validate exact amounts
        total_splits = Decimal('0')
        for split in splits:
            try:
                amount = Decimal(str(split.get('amount', 0)))
                if amount <= 0:
                    errors.append(f"Split amount for {split.get('person', 'unknown')} must be greater than 0")
                total_splits += amount
            except (InvalidOperation, ValueError):
                errors.append(f"Invalid amount for {split.get('person', 'unknown')}")
        
        if total_amount and abs(total_splits - Decimal(str(total_amount))) > Decimal('0.01'):
            errors.append(f"Split amounts ({total_splits}) must equal total expense amount ({total_amount})")
    
    elif split_method == 'percentage':
        # Validate percentages
        total_percentage = Decimal('0')
        for split in splits:
            try:
                percentage = Decimal(str(split.get('percentage', 0)))
                if percentage <= 0 or percentage > 100:
                    errors.append(f"Percentage for {split.get('person', 'unknown')} must be between 0 and 100")
                total_percentage += percentage
            except (InvalidOperation, ValueError):
                errors.append(f"Invalid percentage for {split.get('person', 'unknown')}")
        
        if abs(total_percentage - Decimal('100')) > Decimal('0.01'):
            errors.append(f"Percentages must total 100% (current total: {total_percentage}%)")
    
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
        
        # Determine split method
        split_method_str = data.get('split_method', 'equal')
        split_method = SplitMethod(split_method_str)
        
        # Create the expense
        expense = Expense(
            amount=Decimal(str(data['amount'])),
            description=data['description'].strip(),
            paid_by_id=person.id,
            split_method=split_method
        )
        db.session.add(expense)
        db.session.flush()  # Get the expense ID
        
        # Create splits based on method
        if split_method_str == 'equal':
            # Get all people for equal split (or use participants if provided)
            participants = data.get('participants', [paid_by_name])
            if paid_by_name not in participants:
                participants.append(paid_by_name)
            SettlementCalculator.create_equal_splits(expense.id, participants)
        elif split_method_str in ['exact', 'percentage']:
            # Create custom splits
            SettlementCalculator.create_custom_splits(expense.id, data['splits'], split_method_str)
        
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

@api.route('/expenses/<expense_id>', methods=['PUT'])
def update_expense(expense_id):
    """Update an existing expense"""
    try:
        expense = ExpenseModel.find_by_id(expense_id)
        if not expense:
            return create_response(False, None, "Expense not found", 404)
        
        data = request.get_json()
        if not data:
            return create_response(False, None, "Request body is required", 400)
        
        # Validate input if provided
        if 'amount' in data or 'description' in data or 'paid_by' in data:
            payer = PersonModel.find_by_id(str(expense['paid_by_id']))
            validation_data = {
                'amount': data.get('amount', float(expense['amount'])),
                'description': data.get('description', expense['description']),
                'paid_by': data.get('paid_by', payer['name'] if payer else '')
            }
            
            errors = validate_expense_data(validation_data)
            if errors:
                return create_response(False, None, "; ".join(errors), 400)
        
        # Prepare updates
        updates = {}
        if 'amount' in data:
            updates['amount'] = float(data['amount'])
        if 'description' in data:
            updates['description'] = data['description'].strip()
        if 'split_method' in data:
            updates['split_method'] = data['split_method']
        if 'paid_by' in data:
            paid_by_name = data['paid_by'].strip()
            person = PersonModel.get_or_create(paid_by_name)
            updates['paid_by_id'] = str(person['_id'])
        
        # Update the expense
        if updates:
            ExpenseModel.update(expense_id, updates)
        
        # If amount changed or split method/participants changed, recreate splits
        if 'amount' in data or 'participants' in data or 'split_method' in data or 'splits' in data:
            split_method_str = data.get('split_method', expense['split_method'])
            
            if split_method_str == 'equal':
                payer = PersonModel.find_by_id(str(updates.get('paid_by_id', expense['paid_by_id'])))
                participants = data.get('participants', [payer['name'] if payer else ''])
                if payer and payer['name'] not in participants:
                    participants.append(payer['name'])
                from split_calculator import SplitCalculator
                SplitCalculator.create_equal_splits(expense_id, participants)
            elif split_method_str in ['exact', 'percentage'] and 'splits' in data:
                from split_calculator import SplitCalculator
                SplitCalculator.create_custom_splits(expense_id, data['splits'], split_method_str)
        
        # Get updated expense
        updated_expense = ExpenseModel.find_by_id(expense_id)
        return create_response(True, ExpenseModel.to_dict(updated_expense), "Expense updated successfully")
        
    except Exception as e:
        logging.error(f"Error updating expense: {str(e)}")
        return create_response(False, None, f"Internal server error: {str(e)}", 500)

@api.route('/expenses/<expense_id>', methods=['DELETE'])
def delete_expense(expense_id):
    """Delete an expense"""
    try:
        expense = ExpenseModel.find_by_id(expense_id)
        if not expense:
            return create_response(False, None, "Expense not found", 404)
        
        success = ExpenseModel.delete(expense_id)
        if success:
            return create_response(True, None, "Expense deleted successfully")
        else:
            return create_response(False, None, "Failed to delete expense", 500)
        
    except Exception as e:
        logging.error(f"Error deleting expense: {str(e)}")
        return create_response(False, None, f"Internal server error: {str(e)}", 500)

@api.route('/people', methods=['GET'])
def get_people():
    """Get all people"""
    try:
        people = PersonModel.get_all()
        people_data = []
        for person in people:
            people_data.append({
                'id': str(person['_id']),
                'name': person['name'],
                'created_at': person['created_at'].isoformat() if person.get('created_at') else None
            })
        
        return create_response(True, people_data, "People retrieved successfully")
        
    except Exception as e:
        logging.error(f"Error retrieving people: {str(e)}")
        return create_response(False, None, f"Internal server error: {str(e)}", 500)

@api.route('/balances', methods=['GET'])
def get_balances():
    """Get current balances for all people"""
    try:
        balances = BalanceCalculator.calculate_balances()
        balances_list = list(balances.values())
        
        return create_response(True, balances_list, "Balances calculated successfully")
        
    except Exception as e:
        logging.error(f"Error calculating balances: {str(e)}")
        return create_response(False, None, f"Internal server error: {str(e)}", 500)

@api.route('/settlements', methods=['GET'])
def get_settlements():
    """Get optimal settlements to balance all debts"""
    try:
        settlements = BalanceCalculator.calculate_settlements()
        
        return create_response(True, settlements, "Settlements calculated successfully")
        
    except Exception as e:
        logging.error(f"Error calculating settlements: {str(e)}")
        return create_response(False, None, f"Internal server error: {str(e)}", 500)

# Health check endpoint
@api.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return create_response(True, {"status": "healthy"}, "Service is running")
