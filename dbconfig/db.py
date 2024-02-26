import pymongo
try:
        
    client = pymongo.MongoClient("mongodb://localhost:27017")
        
except Exception as Error:
    print(f"DataBase connection error: {Error}")
        
    
db = client['library2']
books = db['books']
users = db['user']
borrowed_books = db['borrowed_books']