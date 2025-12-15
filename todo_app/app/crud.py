from sqlalchemy.orm import Session
from . import models, schemas


def create_todo_item(db: Session, item: schemas.TodoItemCreate):
    db_item = models.TodoItem(**item.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


def get_todo_items(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.TodoItem).offset(skip).limit(limit).all()


def get_todo_item(db: Session, item_id: int):
    return db.query(models.TodoItem).filter(models.TodoItem.id == item_id).first()


def update_todo_item(
        db: Session,
        item_id: int,
        item_update: schemas.TodoItemUpdate
):
    db_item = get_todo_item(db, item_id)
    if not db_item:
        return None

    update_data = item_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_item, field, value)

    db.commit()
    db.refresh(db_item)
    return db_item


def delete_todo_item(db: Session, item_id: int):
    db_item = get_todo_item(db, item_id)
    if not db_item:
        return False

    db.delete(db_item)
    db.commit()
    return True