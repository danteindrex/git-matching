# Use official Python image
FROM python:3.11-slim

# Set environment variables for predictable Python behavior
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy Django project code into the container
COPY . /app/

# Expose Django port (default 8000)
EXPOSE 8000


# Run migrations and start the Gunicorn web server
CMD ["sh", "-c", "python manage.py migrate && gunicorn django_backend.wsgi:application --bind 0.0.0.0:8000"]
