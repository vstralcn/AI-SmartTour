FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .

# Install dependencies only (extract from pyproject.toml)
RUN pip install --no-cache-dir \
    "fastapi>=0.111.0" \
    "uvicorn[standard]>=0.30.0" \
    "websockets>=12.0" \
    "sqlalchemy>=2.0" \
    "asyncpg>=0.29.0" \
    "pydantic>=2.7" \
    "pydantic-settings>=2.3" \
    "openai>=1.30.0" \
    "python-multipart>=0.0.9" \
    "python-jose[cryptography]>=3.3.0" \
    "redis>=5.0" \
    "httpx>=0.27.0"

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
