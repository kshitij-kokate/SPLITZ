from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app import db
from models import Person, Expense, ExpenseSplit
from settlement_calculator import SettlementCalculator
from decimal import Decimal
import logging

web = Blueprint('web', __name__)

@web.route('/')
def index():
    """Homepage with overview"""
    try:
        # Get summary statistics
        total_expenses = Expense.query.count()
        total_people = Person.query.count()
        
        # Get recent expenses
        recent_expenses = Expense.query.order_by(Expense.created_at.desc()).limit(5).all()
        
        # Get current balances
        balances = SettlementCalculator.calculate_balances()
        
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
        expenses = Expense.query.order_by(Expense.created_at.desc()).all()
        people = Person.query.order_by(Person.name).all()
        
        return render_template('expenses.html', expenses=expenses, people=people)
    except Exception as e:
        logging.error(f"Error loading expenses: {str(e)}")
        flash(f"Error loading expenses: {str(e)}", 'error')
        return render_template('expenses.html', expenses=[], people=[])

@web.route('/settlements')
def settlements():
    """Settlements page"""
    try:
        balances = SettlementCalculator.calculate_balances()
        settlements = SettlementCalculator.calculate_settlements()
        
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
        person = Person.query.filter_by(name=paid_by).first()
        if not person:
            person = Person(name=paid_by)
            db.session.add(person)
            db.session.flush()
        
        # Create the expense
        expense = Expense(
            amount=amount_decimal,
            description=description,
            paid_by_id=person.id
        )
        db.session.add(expense)
        db.session.flush()
        
        # Handle participants (default to all people if none selected)
        if not participants:
            participants = [p.name for p in Person.query.all()]
        
        if paid_by not in participants:
            participants.append(paid_by)
        
        # Create equal splits
        SettlementCalculator.create_equal_splits(expense.id, participants)
        
        db.session.commit()
        flash('Expense added successfully', 'success')
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error adding expense: {str(e)}")
        flash(f'Error adding expense: {str(e)}', 'error')
    
    return redirect(url_for('web.expenses'))

@web.route('/delete_expense/<int:expense_id>', methods=['POST'])
def delete_expense(expense_id):
    """Delete an expense"""
    try:
        expense = Expense.query.get(expense_id)
        if not expense:
            flash('Expense not found', 'error')
        else:
            db.session.delete(expense)
            db.session.commit()
            flash('Expense deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error deleting expense: {str(e)}")
        flash(f'Error deleting expense: {str(e)}', 'error')
    
    return redirect(url_for('web.expenses'))
