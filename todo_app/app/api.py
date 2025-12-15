from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager

from .database import engine, get_db
from . import models, schemas, crud

@asynccontextmanager
async def lifespan(app: FastAPI):
    models.Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(lifespan=lifespan)

@app.post("/items/", response_model=schemas.TodoItem)
def create_item(
    item: schemas.TodoItemCreate,
    db: Session = Depends(get_db)
):
    return crud.create_todo_item(db=db, item=item)

@app.get("/items/", response_model=list[schemas.TodoItem])
def read_items(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    items = crud.get_todo_items(db, skip=skip, limit=limit)
    return items

@app.get("/items/{item_id}", response_model=schemas.TodoItem)
def read_item(item_id: int, db: Session = Depends(get_db)):
    db_item = crud.get_todo_item(db, item_id=item_id)
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return db_item

@app.put("/items/{item_id}", response_model=schemas.TodoItem)
def update_item(
    item_id: int,
    item_update: schemas.TodoItemUpdate,
    db: Session = Depends(get_db)
):
    db_item = crud.update_todo_item(db, item_id=item_id, item_update=item_update)
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return db_item

@app.delete("/items/{item_id}")
def delete_item(item_id: int, db: Session = Depends(get_db)):
    success = crud.delete_todo_item(db, item_id=item_id)
    if not success:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"message": "Item deleted successfully"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}