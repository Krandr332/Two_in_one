from sqlalchemy.orm import Session
from . import models, schemas
from .auth import get_password_hash


# User CRUD operations
def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()


def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


# TodoItem CRUD operations
def create_todo_item(db: Session, item: schemas.TodoItemCreate, user_id: int):
    db_item = models.TodoItem(**item.model_dump(), owner_id=user_id)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


def get_todo_items(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.TodoItem).filter(
        models.TodoItem.owner_id == user_id
    ).offset(skip).limit(limit).all()


def get_todo_item(db: Session, item_id: int, user_id: int):
    return db.query(models.TodoItem).filter(
        models.TodoItem.id == item_id,
        models.TodoItem.owner_id == user_id
    ).first()


def update_todo_item(
    db: Session,
    item_id: int,
    item_update: schemas.TodoItemUpdate,
    user_id: int
):
    db_item = get_todo_item(db, item_id, user_id)
    if not db_item:
        return None

    update_data = item_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_item, field, value)

    db.commit()
    db.refresh(db_item)
    return db_item


def delete_todo_item(db: Session, item_id: int, user_id: int):
    db_item = get_todo_item(db, item_id, user_id)
    if not db_item:
        return False

    db.delete(db_item)
    db.commit()
    return True