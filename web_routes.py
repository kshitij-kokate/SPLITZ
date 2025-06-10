from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from mongo_models import PersonModel, ExpenseModel, BalanceCalculator
from split_calculator import SplitCalculator
from decimal import Decimal
import logging

web = Blueprint('web', __name__)

@web.route('/')
def index():
    """Homepage with overview"""
    try:
        # Get summary statistics
        expenses = ExpenseModel.get_all()
        people = PersonModel.get_all()
        total_expenses = len(expenses)
        total_people = len(people)
        
        # Get recent expenses (first 5)
        recent_expenses = []
        for expense in expenses[:5]:
            recent_expenses.append(ExpenseModel.to_dict(expense))
        
        # Get current balances
        balances = BalanceCalculator.calculate_balances()
        
        return render_template('index.html', 
                             total_expenses=total_expenses,
                             total_people=total_people,
                             recent_expenses=recent_expenses,
                             balances=balances)
    except Exception as e:
        logging.error(f"Error loading homepage: {str(e)}")
        flash(f"Error loading data: {str(e)}", 'error')
        return render_template('index.html', 
                             total_expenses=0,
                             total_people=0,
                             recent_expenses=[],
                             balances={})

@web.route('/expenses')
def expenses():
    """Expenses management page"""
    try:
        expenses_raw = ExpenseModel.get_all()
        expenses = [ExpenseModel.to_dict(expense) for expense in expenses_raw]
        people_raw = PersonModel.get_all()
        people = [{'id': str(p['_id']), 'name': p['name']} for p in people_raw]
        
        return render_template('expenses.html', expenses=expenses, people=people)
    except Exception as e:
        logging.error(f"Error loading expenses: {str(e)}")
        flash(f"Error loading expenses: {str(e)}", 'error')
        return render_template('expenses.html', expenses=[], people=[])

@web.route('/settlements')
def settlements():
    """Settlements page"""
    try:
        balances = BalanceCalculator.calculate_balances()
        settlements = BalanceCalculator.calculate_settlements()
        
        return render_template('settlements.html', 
                             balances=balances,
                             settlements=settlements)
    except Exception as e:
        logging.error(f"Error loading settlements: {str(e)}")
        flash(f"Error calculating settlements: {str(e)}", 'error')
        return render_template('settlements.html', 
                             balances={},
                             settlements=[])

@web.route('/add_expense', methods=['POST'])
def add_expense():
    """Add a new expense via web form"""
    try:
        amount = request.form.get('amount')
        description = request.form.get('description')
        paid_by = request.form.get('paid_by')
        participants = request.form.getlist('participants')
        
        # Validation
        if not amount or not description or not paid_by:
            flash('All fields are required', 'error')
            return redirect(url_for('web.expenses'))
        
        try:
            amount_decimal = Decimal(amount)
            if amount_decimal <= 0:
                flash('Amount must be greater than 0', 'error')
                return redirect(url_for('web.expenses'))
        except:
            flash('Invalid amount', 'error')
            return redirect(url_for('web.expenses'))
        
        # Get or create the person who paid
        person = PersonModel.get_or_create(paid_by)
        person_id = str(person['_id'])
        
        # Create the expense
        expense = ExpenseModel.create(
            amount=float(amount_decimal),
            description=description,
            paid_by_id=person_id
        )
        expense_id = str(expense['_id'])
        
        # Handle participants (default to all people if none selected)
        if not participants:
            all_people = PersonModel.get_all()
            participants = [p['name'] for p in all_people]
        
        if paid_by not in participants:
            participants.append(paid_by)
        
        # Create equal splits
        SplitCalculator.create_equal_splits(expense_id, participants)
        
        flash('Expense added successfully', 'success')
        
    except Exception as e:
        logging.error(f"Error adding expense: {str(e)}")
        flash(f'Error adding expense: {str(e)}', 'error')
    
    return redirect(url_for('web.expenses'))

@web.route('/delete_expense/<expense_id>', methods=['POST'])
def delete_expense(expense_id):
    """Delete an expense"""
    try:
        expense = ExpenseModel.find_by_id(expense_id)
        if not expense:
            flash('Expense not found', 'error')
        else:
            success = ExpenseModel.delete(expense_id)
            if success:
                flash('Expense deleted successfully', 'success')
            else:
                flash('Failed to delete expense', 'error')
    except Exception as e:
        logging.error(f"Error deleting expense: {str(e)}")
        flash(f'Error deleting expense: {str(e)}', 'error')
    
    return redirect(url_for('web.expenses'))
