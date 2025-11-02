# FastBG - FastAPI Backend Generator

A modern, async FastAPI backend with automatic CRUD generation, authentication, and Docker deployment. Built with SQLAlchemy, Pydantic, and featuring automatic REST API generation from SQLAlchemy models.

## Features

- **Automatic CRUD API Generation** - Generate complete REST APIs from SQLAlchemy models
- **Soft Delete** - ORM-level soft delete with automatic filtering
- **Automatic Schema Generation** - Pydantic schemas from SQLAlchemy models with validation

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.12 (for local development)

### Using Docker

1. **Clone and setup:**
   ```bash
   git clone <repository-url>
   cd fastbg
   docker-compose up
   ```
2. View API documentation:

    - Swagger UI: http://localhost:8000/docs
    - ReDoc: http://localhost:8000/redoc

### Manual installation

1. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

2. Set environment variables

   ```bash
    export FASTBG_SETTINGS_MODULE="fastbg.conf.dev"
    export PYTHONPATH="$PWD/src"
   ```

3. Run database migrations

   ```bash
   alembic upgrade head
   ```

4. Start development server

   ```bash
   uvicorn fastbg.server:app --reload --host 0.0.0.0 --port 8000
   ```
