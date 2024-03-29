from pydantic import BaseModel

class Book(BaseModel):
    title: str
    author: str
    isbn: str
    quantity: int
    
    
class User(BaseModel):
        username : str
        email : str