from datetime import timedelta
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager

from todo_app.app.database import engine, get_db
from todo_app.app import models, schemas, crud, auth
from todo_app.app.config import ENV

@asynccontextmanager
async def lifespan(app: FastAPI):
    models.Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    lifespan=lifespan,
    title="Todo API",
    description="API для управления задачами с аутентификацией",
    version="1.0.0",

)

@app.post("/register", response_model=schemas.User)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    db_user_email = crud.get_user_by_email(db, email=user.email)
    if db_user_email:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)


@app.post("/auth", response_model=schemas.Token)
def login_for_access_token(
    form_data: schemas.UserLogin,
    db: Session = Depends(get_db)
):
    print(form_data.username, form_data.password)
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ENV.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me", response_model=schemas.User)
def read_users_me(current_user: schemas.User = Depends(auth.get_current_active_user)):
    return current_user


@app.post("/items/", response_model=schemas.TodoItem)
def create_item(
    item: schemas.TodoItemCreate,
    current_user: schemas.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    return crud.create_todo_item(db=db, item=item, user_id=current_user.id)


@app.get("/items/", response_model=list[schemas.TodoItem])
def read_items(
    skip: int = 0,
    limit: int = 100,
    current_user: schemas.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    items = crud.get_todo_items(db, user_id=current_user.id, skip=skip, limit=limit)
    return items


@app.get("/items/{item_id}", response_model=schemas.TodoItem)
def read_item(
    item_id: int,
    current_user: schemas.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    db_item = crud.get_todo_item(db, item_id=item_id, user_id=current_user.id)
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return db_item


@app.put("/items/{item_id}", response_model=schemas.TodoItem)
def update_item(
    item_id: int,
    item_update: schemas.TodoItemUpdate,
    current_user: schemas.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    db_item = crud.update_todo_item(
        db, item_id=item_id, item_update=item_update, user_id=current_user.id
    )
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return db_item


@app.delete("/items/{item_id}")
def delete_item(
    item_id: int,
    current_user: schemas.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    success = crud.delete_todo_item(db, item_id=item_id, user_id=current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"message": "Item deleted successfully"}


@app.get("/items/my/", response_model=list[schemas.TodoItem])
def read_my_items(
        completed: Optional[bool] = None,
        current_user: schemas.User = Depends(auth.get_current_active_user),
        db: Session = Depends(get_db)
):
    """
     completed:
                если True - вернуть только завершенные задачи,
                 если False - вернуть только незавершенные задачи,
                 если None - вернуть все задачи (по умолчанию)
    """
    all_items = crud.get_todo_items(db, user_id=current_user.id, skip=0, limit=100)

    if completed is not None:
        filtered_items = [item for item in all_items if item.completed == completed]
        return filtered_items

    return all_items