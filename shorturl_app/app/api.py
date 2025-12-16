from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import uvicorn

from contextlib import  asynccontextmanager

from . import crud, models
from . import schemas
from .database import get_db, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    models.Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title="URL Shortener Service",
    description="Сервис для сокращения длинных URL",
    version="1.0.0",
    lifespan=lifespan
)


@app.post("/shorten", response_model=schemas.URLInfo)
def create_short_url(
        url_data: schemas.URLCreate,
        request: Request,
        db: Session = Depends(get_db)
):
    """
    - **url**: полный URL для сокращения
    """
    try:
        if not url_data.url.startswith(('http://', 'https://')):
            url_data.url = 'http://' + url_data.url

        url_mapping = crud.create_short_url(db, url_data.url)

        base_url = str(request.base_url)
        short_url = f"{base_url}{url_mapping.short_id}"

        return {
            "short_id": url_mapping.short_id,
            "original_url": url_mapping.original_url,
            "created_at": url_mapping.created_at,
            "clicks": url_mapping.clicks,
            "short_url": short_url
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка создания короткой ссылки: {str(e)}")


@app.get("/{short_id}")
def redirect_to_original(
        short_id: str,
        request: Request,
        db: Session = Depends(get_db)
):
    """
    Перенаправление по короткой ссылке

    - **short_id**: короткий идентификатор ссылки
    """
    url_mapping = crud.get_url_by_short_id(db, short_id)

    if not url_mapping:
        raise HTTPException(status_code=404, detail="Ссылка не найдена или деактивирована")

    crud.increment_clicks(db, url_mapping)

    return RedirectResponse(url=url_mapping.original_url)


@app.get("/stats/{short_id}", response_model=schemas.URLStats)
def get_url_statistics(
        short_id: str,
        db: Session = Depends(get_db)
):
    """
    Получение статистики по короткой ссылке

    - **short_id**: короткий идентификатор ссылки
    """
    url_mapping = crud.get_url_stats(db, short_id)

    if not url_mapping:
        raise HTTPException(status_code=404, detail="Ссылка не найдена")

    return url_mapping


@app.delete("/{short_id}")
def delete_short_url(
        short_id: str,
        db: Session = Depends(get_db)
):
    """
    - **short_id**: короткий идентификатор ссылки
    """
    success = crud.delete_url(db, short_id)

    if not success:
        raise HTTPException(status_code=404, detail="Ссылка не найдена")

    return {"message": "Ссылка успешно удалена", "short_id": short_id}


@app.get("/")
def root():
    return {
        "message": "URL Shortener Service",
        "documentation": "/docs",
        "endpoints": {
            "create_short_url": "POST /shorten",
            "redirect": "GET /{short_id}",
            "get_stats": "GET /stats/{short_id}",
            "delete_url": "DELETE /{short_id}"
        }
    }


