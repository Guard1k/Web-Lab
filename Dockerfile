# 1. Базовий образ з Python
FROM python:3.11-slim

# 2. Встановлюємо залежності системи для psycopg2
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 3. Створюємо робочу директорію
WORKDIR /app

# 4. Копіюємо файли проекту
COPY requirements.txt .

# 5. Встановлюємо Python-залежності
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 6. Вказуємо порт Flask-сервера
EXPOSE 3000

# 7. Запуск Flask
CMD ["python", "web.py"]
