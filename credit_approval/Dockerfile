FROM python:3.12.2-slim

# Install PostgreSQL development package
RUN apt-get update && apt-get install -y postgresql-server-dev-all

WORKDIR /app

COPY requirements.txt /app/requirements.txt

RUN pip install --upgrade pip

RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
