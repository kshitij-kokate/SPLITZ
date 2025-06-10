from mongo_models import PersonModel, ExpenseModel, ExpenseSplitModel
from database import SplitMethod
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict

class SplitCalculator:
    """Calculate and create expense splits for MongoDB"""
    
    @staticmethod
    def create_equal_splits(expense_id: str, participant_names: List[str]) -> None:
        """Create equal splits for an expense among participants"""
        expense = ExpenseModel.find_by_id(expense_id)
        if not expense:
            raise ValueError("Expense not found")
        
        # Clear existing splits
        ExpenseSplitModel.delete_by_expense(expense_id)
        
        # Calculate equal split amount
        total_amount = expense['amount']
        num_participants = len(participant_names)
        split_amount = (total_amount / num_participants).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        # Handle rounding by adjusting the last split
        total_splits = split_amount * (num_participants - 1)
        last_split_amount = total_amount - total_splits
        
        for i, name in enumerate(participant_names):
            person = PersonModel.get_or_create(name.strip())
            person_id = str(person['_id'])
            
            amount = last_split_amount if i == num_participants - 1 else split_amount
            percentage = Decimal('100') / num_participants
            
            ExpenseSplitModel.create(
                expense_id=expense_id,
                person_id=person_id,
                amount=float(amount),
                percentage=float(percentage)
            )
    
    @staticmethod
    def create_custom_splits(expense_id: str, splits_data: List[Dict], split_method: str) -> None:
        """Create custom splits for an expense (exact amounts or percentages)"""
        expense = ExpenseModel.find_by_id(expense_id)
        if not expense:
            raise ValueError("Expense not found")
        
        # Clear existing splits
        ExpenseSplitModel.delete_by_expense(expense_id)
        
        created_splits = []
        
        for split_data in splits_data:
            person_name = split_data['person'].strip()
            person = PersonModel.get_or_create(person_name)
            person_id = str(person['_id'])
            
            if split_method == SplitMethod.EXACT:
                # Use the provided exact amount
                split_amount = Decimal(str(split_data['amount'])).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                percentage = (split_amount / expense['amount'] * 100).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            elif split_method == SplitMethod.PERCENTAGE:
                # Calculate amount from percentage
                percentage = Decimal(str(split_data['percentage'])).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                split_amount = (expense['amount'] * percentage / 100).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            else:
                raise ValueError(f"Invalid split method: {split_method}")
            
            split = ExpenseSplitModel.create(
                expense_id=expense_id,
                person_id=person_id,
                amount=float(split_amount),
                percentage=float(percentage)
            )
            created_splits.append(split)
        
        # Handle rounding differences for exact amounts
        if split_method == SplitMethod.EXACT:
            splits = ExpenseSplitModel.find_by_expense(expense_id)
            total_splits = sum(Decimal(str(split['amount'])) for split in splits)
            diff = expense['amount'] - total_splits
            
            if abs(diff) > Decimal('0.01') and splits:
                # Adjust the first split to handle rounding
                first_split = splits[0]
                new_amount = Decimal(str(first_split['amount'])) + diff
                new_percentage = (new_amount / expense['amount'] * 100).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                
                # Update the split in database
                from database import mongo, EXPENSE_SPLITS_COLLECTION
                from bson import ObjectId
                mongo.db[EXPENSE_SPLITS_COLLECTION].update_one(
                    {'_id': first_split['_id']},
                    {'$set': {
                        'amount': new_amount,
                        'percentage': new_percentage
                    }}
                )
        
        # Handle rounding differences for percentage amounts
        elif split_method == SplitMethod.PERCENTAGE:
            splits = ExpenseSplitModel.find_by_expense(expense_id)
            total_splits = sum(Decimal(str(split['amount'])) for split in splits)
            diff = expense['amount'] - total_splits
            
            if abs(diff) > Decimal('0.01') and splits:
                # Adjust the last split to handle rounding
                last_split = splits[-1]
                new_amount = Decimal(str(last_split['amount'])) + diff
                
                # Update the split in database
                from database import mongo, EXPENSE_SPLITS_COLLECTION
                from bson import ObjectId
                mongo.db[EXPENSE_SPLITS_COLLECTION].update_one(
                    {'_id': last_split['_id']},
                    {'$set': {'amount': new_amount}}
                )