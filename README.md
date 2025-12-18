# Локальный запуск:
## todo:

1 - `cd .\todo_app\` 
2 - `uvicorn app.api:app --host 0.0.0.0 --port 8000 --reload`

## short_url
1 - `cd .\shorturl_app\`
2 - `uvicorn app.api:app --host 0.0.0.0 --port 8001 --reload`

# Docker запуск

`docker compose up -d`

Докер образ уже отправлен в dockerhub, поэтому в docker compose я не build образы

# Тесты 

команда для запуска - `pytest`