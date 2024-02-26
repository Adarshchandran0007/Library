from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import  HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import uvicorn
import pymongo
from datetime import datetime
from dbconfig.db import users, books, borrowed_books
from models.models import User,Book

app = APIRouter()

templates = Jinja2Templates(directory="templates")

# def bson_to_str(obj):
#     if isinstance(obj, dict):
#         for key, value in obj.items():
#             if isinstance(value, ObjectId):
#                 obj[key] = str(value)
#     return obj



@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/add-book-form", response_class=HTMLResponse, tags=['Forms'])
async def add_book_form(request: Request):
    return templates.TemplateResponse("add_books.html", {"request": request})


@app.post("/books", tags=['Book'])
async def add_book(title: str = Form(...), author: str = Form(...), isbn: str = Form(...), quantity: int = Form(...)):
    # Check if the book already exists
    existing_book = books.find_one({"title": title})
    if existing_book:
        # If the book exists, update its quantity
        new_quantity = existing_book.get("quantity", 0) + quantity
        books.update_one({"title": title}, {"$set": {"quantity": new_quantity}})
        return {"message": f"Quantity of '{title}' updated successfully."}
    else:
        # If the book doesn't exist, insert a new document
        book_data = {"title": title, "author": author, "isbn": isbn, "quantity": quantity}
        books.insert_one(book_data)
        return {"message": "Book added successfully."}


@app.get("/books", tags=['Book'])
async def view_all_books():
    try:
        all_book = list(books.find())
        for book in all_book:
            book['_id']=str(book['_id'])
        return all_book
    except Exception as e:
        return{"Error:an unexpected error occurred"}

@app.get("/add-user-form", response_class=HTMLResponse, tags=['Forms'])
async def add_user_form(request: Request):
    return templates.TemplateResponse("add_users.html", {"request": request})



@app.post('/user', tags=['User'])
async def add_user(username: str = Form(...), email: str = Form(...)):
    try:
        # Check if user already exists
        existing_user = users.find_one({'username': username})
        if existing_user:
            raise HTTPException(status_code=400, detail="User already exists change user name")

        # If user does not exist, insert the new user
        user_data = User(username=username, email=email)
        users.insert_one(user_data.dict())
        
        return {'message': 'User added successfully'}
    except Exception as e:
         return {"error": "An unexpected error occurred."}
    
@app.get("/users", tags=['User'])
async def view_all_users():
    try:
        all_users = list(users.find())
        for user in all_users:
            user['_id']=str(user['_id'])
        return all_users
    except Exception as e:
        return{"Error: an unexpected error occurred"}
    
    
@app.delete("/user/{username}", tags=['User'])
async def delete_user(username: str):
    try:
        # Check if the user exists
        existing_user = users.find_one({'username': username})
        if not existing_user:
            raise HTTPException(status_code=404, detail="User not found")

        # Delete the user
        users.delete_one({'username': username})

        return {"message": f"User '{username}' deleted successfully"}
    
    except pymongo.errors.PyMongoError as e:
        # Handle MongoDB errors
        return {"error": "An error occurred while accessing the database."}

    except Exception as e:
        # Handle other unexpected errors
        return {"error": "An unexpected error occurred."}
    

@app.get('/borrow-form',response_class=HTMLResponse, tags=['Forms'])
async def borrow_book_form(request:Request):
    return templates.TemplateResponse('borrow_book.html',{'request':request})


@app.post("/borrow", tags=['Book'])
async def borrow_book(title: str = Form(...), username: str = Form(...)):
    # Check if the user exists
    user = users.find_one({'username': username})
    if not user:
        return JSONResponse(content={"message": "User not found."}, status_code=404)
    
    # Check if the book exists and is available
    book = books.find_one({"title": title, "quantity": {"$gt": 0}})
    if not book:
        return JSONResponse(content={"message": f"'{title}' is not available for borrowing."}, status_code=404)
    
    # Check if the book is already borrowed by the user
    existing_borrowed_book = borrowed_books.find_one({"title": title, "username": username})
    if existing_borrowed_book:
        return JSONResponse(content={"message": f"{username} has already borrowed '{title}'."}, status_code=400)
    
    # Decrease the quantity of the book
    books.update_one({"title": title}, {"$inc": {"quantity": -1}})
    
    # Record the borrowing details
    borrowed_book_data = {
        'username': username,
        'title': title,
        'borrow_date': datetime.now()
    }
    borrowed_books.insert_one(borrowed_book_data)
    
    return {"message": f"{username} has borrowed '{title}'."}


@app.get('/return-form',response_class=HTMLResponse, tags=['Forms'])
async def return_book_form(request:Request):
    return templates.TemplateResponse('return_book.html',{'request':request})


@app.post('/return',tags=['Book'])
async def return_book( username: str = Form(...), title: str= Form(...)):
        borrowed_book = borrowed_books.find_one({'username': username, 'title': title})
        if borrowed_book:
            borrowed_books.delete_one({'username': username, 'title': title})
            existing_book = books.find_one({'title': title})
            if existing_book:                                                  #check if book is existing if found add quantity
                books.update_one({'_id': existing_book['_id']}, {'$inc': {'quantity': 1}})
                return(f"Updated quantity of book '{title}'.")
            else:                                                              #insert new record if not found
                books.insert_one({'title': title, 'quantity': 1})
                print(f"Added new book '{title}' to collection.")
            return("Book returned successfully.")
        else:
            return("Book not borrowed by the user.")
        
        
@app.get("/books/borrowed", tags=['Book'])
async def get_borrowed_books():
    borrowed_books_list = list(borrowed_books.find())
    # Convert ObjectId to string for each document
    for book in borrowed_books_list:
        book['_id'] = str(book['_id'])
    return borrowed_books_list


@app.get('/user/borrowed/form',response_class=HTMLResponse, tags=['Forms'])
async def books_borrowed_by_user(request:Request):
    return templates.TemplateResponse('search_user.html',{'request':request})
 
 
    

@app.post("/user/books-borrowed" , tags=['User'])
async def get_borrowed_books(username: str = Form(...)):
    try:
        # Use aggregation to group by username and project the book titles
        pipeline = [
            {"$match": {"username": username}},
            {"$group": {"_id": "$username", "books": {"$push": "$title"}}}
        ]
        result = borrowed_books.aggregate(pipeline)

        # Extract the list of book titles from the aggregation result
        books_borrowed = next(result, None)
        if books_borrowed:
            return books_borrowed["books"]
        else:
            return ('no records found')

    except pymongo.errors.PyMongoError as e:
        # Handle MongoDB errors here
        return {"error": "An error occurred while accessing the database."}

    except Exception as e:
        # Handle other unexpected errors
        return {"error": "An unexpected error occurred."}

# @app.get("/view_borrowed_books")
# async def view_borrowed_books():
#     borrowed_books =borrowed_books.find()
#     borrowed_list = [bson_to_str(i) for i in borrowed_books]
#     return borrowed_list

if __name__ == "__main__":
    uvicorn.run("main2:app", host="0.0.0.0", port=8000)