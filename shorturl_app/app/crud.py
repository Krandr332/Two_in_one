from sqlalchemy.orm import Session
from .models import URLMapping


def create_short_url(db: Session, url: str) -> URLMapping:
    """Создание короткой ссылки"""
    existing_url = db.query(URLMapping).filter(
        URLMapping.original_url == url,
        URLMapping.is_active == True
    ).first()

    if existing_url:
        return existing_url

    db_url = URLMapping(original_url=url)

    while db.query(URLMapping).filter(URLMapping.short_id == db_url.short_id).first():
        db_url.short_id = URLMapping.generate_short_id()

    db.add(db_url)
    db.commit()
    db.refresh(db_url)
    return db_url


def get_url_by_short_id(db: Session, short_id: str) -> URLMapping:
    """Получение URL по короткому идентификатору"""
    return db.query(URLMapping).filter(
        URLMapping.short_id == short_id,
        URLMapping.is_active == True
    ).first()


def increment_clicks(db: Session, url_mapping: URLMapping) -> None:
    """Увеличение счетчика кликов"""
    url_mapping.clicks += 1
    db.commit()
    db.refresh(url_mapping)


def get_url_stats(db: Session, short_id: str) -> URLMapping:
    """Получение статистики по короткой ссылке"""
    return db.query(URLMapping).filter(URLMapping.short_id == short_id).first()


def delete_url(db: Session, short_id: str) -> bool:
    """Полное удаление ссылки из базы данных"""
    url_mapping = db.query(URLMapping).filter(URLMapping.short_id == short_id).first()
    if url_mapping:
        db.delete(url_mapping)
        db.commit()
        return True
    return False