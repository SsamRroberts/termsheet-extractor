# Use the official Python image from the Docker Hub
FROM python:3.12-slim

# Set environment variables
ENV ENVIRONMENT=${ENVIRONMENT}
ENV POETRY_VERSION=2.2.1
ENV PATH="/root/.local/bin:$PATH"

RUN /bin/sh -c 'echo "The environment is: $ENVIRONMENT"'

# POSTGRES system dependencies
# build-essential for psycopg2
# libpq-dev for pg_config
# postgresql-client for pg_dump
RUN apt-get update \
    && apt-get install -y \
        build-essential \
        libpq-dev \
        postgresql-client \
    && rm -rf /var/lib/apt/lists/*


# Install Poetry
RUN pip install --no-cache-dir poetry==${POETRY_VERSION}

# Configure poetry to not create virtual environment
RUN poetry config virtualenvs.create false

# Set working directory in the container
RUN mkdir /backend
WORKDIR /backend

# Copy poetry files first for better caching
COPY pyproject.toml poetry.lock* /backend/

# Install the dependencies
RUN poetry install --without dev

# Pin packaging after poetry install (dependencies upgrade it)
RUN pip install --no-cache-dir --force-reinstall "packaging<25.0"

# Copy the rest of your application code
COPY . /backend/

# Expose the port the app runs on
EXPOSE 8000

# Run the FastAPI application with uvicorn
CMD ["poetry", "run", "uvicorn", "main:fastapp", "--host", "0.0.0.0", "--port", "8000"]
