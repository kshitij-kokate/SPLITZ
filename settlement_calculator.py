from decimal import Decimal, ROUND_HALF_UP
from collections import defaultdict
from typing import List, Dict, Tuple
from models import Person, Expense, ExpenseSplit

class SettlementCalculator:
    """
    Calculates optimal settlements to minimize the number of transactions needed
    to settle all debts between people in the group.
    """
    
    @staticmethod
    def calculate_balances() -> Dict[str, Dict]:
        """
        Calculate each person's balance (total_paid - fair_share).
        Returns a dictionary with person names as keys and balance info as values.
        """
        balances = {}
        
        # Get all people who have been involved in expenses
        people = Person.query.all()
        
        for person in people:
            total_paid = Decimal('0')
            fair_share = Decimal('0')
            
            # Calculate total paid by this person
            for expense in person.expenses_paid:
                total_paid += expense.amount
            
            # Calculate fair share (total amount they should pay based on splits)
            for split in person.expense_splits:
                fair_share += split.amount
            
            balance = total_paid - fair_share
            
            balances[person.name] = {
                'name': person.name,
                'total_paid': float(total_paid),
                'fair_share': float(fair_share),
                'balance': float(balance)  # Positive means they are owed money, negative means they owe money
            }
        
        return balances
    
    @staticmethod
    def calculate_settlements() -> List[Dict]:
        """
        Calculate the minimal set of transactions to settle all balances.
        Uses a greedy algorithm to minimize the number of transactions.
        """
        balances = SettlementCalculator.calculate_balances()
        
        # Separate creditors (positive balance) and debtors (negative balance)
        creditors = []  # People who are owed money
        debtors = []    # People who owe money
        
        for person_name, balance_info in balances.items():
            balance = Decimal(str(balance_info['balance'])).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            
            if balance > 0:
                creditors.append({'name': person_name, 'amount': balance})
            elif balance < 0:
                debtors.append({'name': person_name, 'amount': abs(balance)})
        
        settlements = []
        
        # Sort by amount (largest first) to minimize transactions
        creditors.sort(key=lambda x: x['amount'], reverse=True)
        debtors.sort(key=lambda x: x['amount'], reverse=True)
        
        i, j = 0, 0
        
        while i < len(creditors) and j < len(debtors):
            creditor = creditors[i]
            debtor = debtors[j]
            
            # Calculate the settlement amount (minimum of what creditor is owed and debtor owes)
            settlement_amount = min(creditor['amount'], debtor['amount'])
            
            if settlement_amount > Decimal('0.01'):  # Only create settlement if amount is significant
                settlements.append({
                    'from': debtor['name'],
                    'to': creditor['name'],
                    'amount': float(settlement_amount)
                })
                
                # Update remaining amounts
                creditor['amount'] -= settlement_amount
                debtor['amount'] -= settlement_amount
            
            # Move to next creditor/debtor if current one is settled
            if creditor['amount'] <= Decimal('0.01'):
                i += 1
            if debtor['amount'] <= Decimal('0.01'):
                j += 1
        
        return settlements
    
    @staticmethod
    def create_equal_splits(expense_id: int, participant_names: List[str]) -> None:
        """
        Create equal splits for an expense among the specified participants.
        """
        from app import db
        
        expense = Expense.query.get(expense_id)
        if not expense:
            raise ValueError("Expense not found")
        
        # Clear existing splits
        ExpenseSplit.query.filter_by(expense_id=expense_id).delete()
        
        # Calculate equal split amount
        split_amount = (expense.amount / len(participant_names)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        # Handle rounding by adjusting the last split
        total_splits = split_amount * (len(participant_names) - 1)
        last_split_amount = expense.amount - total_splits
        
        for i, name in enumerate(participant_names):
            person = Person.query.filter_by(name=name).first()
            if not person:
                person = Person(name=name)
                db.session.add(person)
                db.session.flush()  # Get the ID
            
            amount = last_split_amount if i == len(participant_names) - 1 else split_amount
            
            split = ExpenseSplit(
                expense_id=expense_id,
                person_id=person.id,
                amount=amount,
                percentage=Decimal('100') / len(participant_names)
            )
            db.session.add(split)
        
        db.session.commit()
