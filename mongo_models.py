from database import mongo, MongoEncoder, SplitMethod, PEOPLE_COLLECTION, EXPENSES_COLLECTION, EXPENSE_SPLITS_COLLECTION
from datetime import datetime
from bson import ObjectId
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Optional

class PersonModel:
    """MongoDB model for Person documents"""
    
    @staticmethod
    def create(name: str) -> Dict:
        """Create a new person"""
        person = {
            'name': name.strip(),
            'created_at': datetime.utcnow()
        }
        result = mongo.db[PEOPLE_COLLECTION].insert_one(person)
        person['_id'] = result.inserted_id
        return person
    
    @staticmethod
    def find_by_name(name: str) -> Optional[Dict]:
        """Find person by name"""
        return mongo.db[PEOPLE_COLLECTION].find_one({'name': name.strip()})
    
    @staticmethod
    def find_by_id(person_id: str) -> Optional[Dict]:
        """Find person by ID"""
        try:
            return mongo.db[PEOPLE_COLLECTION].find_one({'_id': ObjectId(person_id)})
        except:
            return None
    
    @staticmethod
    def get_all() -> List[Dict]:
        """Get all people"""
        return list(mongo.db[PEOPLE_COLLECTION].find().sort('name', 1))
    
    @staticmethod
    def get_or_create(name: str) -> Dict:
        """Get existing person or create new one"""
        person = PersonModel.find_by_name(name)
        if not person:
            person = PersonModel.create(name)
        return person

class ExpenseModel:
    """MongoDB model for Expense documents"""
    
    @staticmethod
    def create(amount: float, description: str, paid_by_id: str, split_method: str = SplitMethod.EQUAL) -> Dict:
        """Create a new expense"""
        expense = {
            'amount': Decimal(str(amount)),
            'description': description.strip(),
            'paid_by_id': ObjectId(paid_by_id),
            'split_method': split_method,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        result = mongo.db[EXPENSES_COLLECTION].insert_one(expense)
        expense['_id'] = result.inserted_id
        return expense
    
    @staticmethod
    def find_by_id(expense_id: str) -> Optional[Dict]:
        """Find expense by ID"""
        try:
            return mongo.db[EXPENSES_COLLECTION].find_one({'_id': ObjectId(expense_id)})
        except:
            return None
    
    @staticmethod
    def get_all() -> List[Dict]:
        """Get all expenses"""
        return list(mongo.db[EXPENSES_COLLECTION].find().sort('created_at', -1))
    
    @staticmethod
    def update(expense_id: str, updates: Dict) -> bool:
        """Update an expense"""
        try:
            updates['updated_at'] = datetime.utcnow()
            prepared_updates = MongoEncoder.prepare_for_mongo(updates)
            result = mongo.db[EXPENSES_COLLECTION].update_one(
                {'_id': ObjectId(expense_id)},
                {'$set': prepared_updates}
            )
            return result.modified_count > 0
        except:
            return False
    
    @staticmethod
    def delete(expense_id: str) -> bool:
        """Delete an expense"""
        try:
            # Delete associated splits first
            ExpenseSplitModel.delete_by_expense(expense_id)
            
            result = mongo.db[EXPENSES_COLLECTION].delete_one({'_id': ObjectId(expense_id)})
            return result.deleted_count > 0
        except:
            return False
    
    @staticmethod
    def to_dict(expense: Dict) -> Dict:
        """Convert expense document to API response format"""
        if not expense:
            return None
        
        # Get payer information
        payer = PersonModel.find_by_id(str(expense['paid_by_id']))
        
        # Get splits
        splits = ExpenseSplitModel.find_by_expense(str(expense['_id']))
        
        return {
            'id': str(expense['_id']),
            'amount': float(expense['amount']),
            'description': expense['description'],
            'paid_by': payer['name'] if payer else 'Unknown',
            'paid_by_id': str(expense['paid_by_id']),
            'split_method': expense['split_method'],
            'created_at': expense['created_at'].isoformat() if expense.get('created_at') else None,
            'updated_at': expense['updated_at'].isoformat() if expense.get('updated_at') else None,
            'splits': [ExpenseSplitModel.to_dict(split) for split in splits]
        }

class ExpenseSplitModel:
    """MongoDB model for ExpenseSplit documents"""
    
    @staticmethod
    def create(expense_id: str, person_id: str, amount: float, percentage: Optional[float] = None) -> Dict:
        """Create a new expense split"""
        split = {
            'expense_id': ObjectId(expense_id),
            'person_id': ObjectId(person_id),
            'amount': Decimal(str(amount)),
            'percentage': Decimal(str(percentage)) if percentage else None
        }
        result = mongo.db[EXPENSE_SPLITS_COLLECTION].insert_one(split)
        split['_id'] = result.inserted_id
        return split
    
    @staticmethod
    def find_by_expense(expense_id: str) -> List[Dict]:
        """Find all splits for an expense"""
        try:
            return list(mongo.db[EXPENSE_SPLITS_COLLECTION].find({'expense_id': ObjectId(expense_id)}))
        except:
            return []
    
    @staticmethod
    def find_by_person(person_id: str) -> List[Dict]:
        """Find all splits for a person"""
        try:
            return list(mongo.db[EXPENSE_SPLITS_COLLECTION].find({'person_id': ObjectId(person_id)}))
        except:
            return []
    
    @staticmethod
    def delete_by_expense(expense_id: str) -> bool:
        """Delete all splits for an expense"""
        try:
            mongo.db[EXPENSE_SPLITS_COLLECTION].delete_many({'expense_id': ObjectId(expense_id)})
            return True
        except:
            return False
    
    @staticmethod
    def to_dict(split: Dict) -> Dict:
        """Convert split document to API response format"""
        if not split:
            return None
        
        # Get person information
        person = PersonModel.find_by_id(str(split['person_id']))
        
        return {
            'id': str(split['_id']),
            'expense_id': str(split['expense_id']),
            'person_id': str(split['person_id']),
            'person_name': person['name'] if person else 'Unknown',
            'amount': float(split['amount']),
            'percentage': float(split['percentage']) if split.get('percentage') else None
        }

class BalanceCalculator:
    """Calculate balances and settlements using MongoDB data"""
    
    @staticmethod
    def calculate_balances() -> Dict[str, Dict]:
        """Calculate each person's balance (total_paid - fair_share)"""
        balances = {}
        
        # Get all people
        people = PersonModel.get_all()
        
        for person in people:
            person_id = str(person['_id'])
            person_name = person['name']
            
            # Calculate total paid by this person
            total_paid = Decimal('0')
            expenses = mongo.db[EXPENSES_COLLECTION].find({'paid_by_id': person['_id']})
            for expense in expenses:
                total_paid += expense['amount']
            
            # Calculate fair share (total amount they should pay based on splits)
            fair_share = Decimal('0')
            splits = ExpenseSplitModel.find_by_person(person_id)
            for split in splits:
                fair_share += split['amount']
            
            balance = total_paid - fair_share
            
            balances[person_name] = {
                'name': person_name,
                'total_paid': float(total_paid),
                'fair_share': float(fair_share),
                'balance': float(balance)
            }
        
        return balances
    
    @staticmethod
    def calculate_settlements() -> List[Dict]:
        """Calculate optimal settlements to minimize transactions"""
        balances = BalanceCalculator.calculate_balances()
        
        # Separate creditors and debtors
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
            
            # Calculate settlement amount
            settlement_amount = min(creditor['amount'], debtor['amount'])
            
            if settlement_amount > Decimal('0.01'):
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