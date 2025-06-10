from flask_pymongo import PyMongo
from datetime import datetime
from bson import ObjectId
from decimal import Decimal
import os

# MongoDB instance will be initialized in app.py
mongo = None

def init_db(app):
    """Initialize MongoDB connection"""
    global mongo
    app.config["MONGO_URI"] = os.environ.get("MONGO_URI", "mongodb://localhost:27017/splitapp")
    mongo = PyMongo(app)
    return mongo

class MongoEncoder:
    """Helper class for MongoDB document serialization"""
    
    @staticmethod
    def to_dict(doc):
        """Convert MongoDB document to dictionary with proper serialization"""
        if not doc:
            return None
        
        result = {}
        for key, value in doc.items():
            if isinstance(value, ObjectId):
                result[key] = str(value)
            elif isinstance(value, datetime):
                result[key] = value.isoformat()
            elif isinstance(value, Decimal):
                result[key] = float(value)
            else:
                result[key] = value
        return result
    
    @staticmethod
    def prepare_for_mongo(data):
        """Prepare data for MongoDB insertion"""
        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                if isinstance(value, str) and key.endswith('_id') and key != '_id':
                    try:
                        result[key] = ObjectId(value)
                    except:
                        result[key] = value
                elif isinstance(value, (int, float)) and key in ['amount', 'percentage']:
                    result[key] = Decimal(str(value))
                else:
                    result[key] = value
            return result
        return data

class SplitMethod:
    """Enum-like class for split methods"""
    EQUAL = "equal"
    EXACT = "exact"
    PERCENTAGE = "percentage"
    
    @classmethod
    def is_valid(cls, method):
        return method in [cls.EQUAL, cls.EXACT, cls.PERCENTAGE]

# Collection names
PEOPLE_COLLECTION = "people"
EXPENSES_COLLECTION = "expenses"
EXPENSE_SPLITS_COLLECTION = "expense_splits"