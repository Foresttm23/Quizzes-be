# Quiz Management System

A backend service for managing quizzes, built with **FastAPI**, **PostgreSQL**, **SQLAlchemy**, **Redis**, and **JWT-based authentication**. The project supports both local authentication and **Auth0** login, and is structured around separate service and repository layers for maintainability.

## Overview

The system is designed with a layered architecture, caching, and asynchronous processing to support scalable backend workflows.

## Technologies Used

- **Core:** Python 3.13+, FastAPI, Pydantic v2
- **Data:** PostgreSQL, asynchronous SQLAlchemy, Alembic
- **Performance:** Redis, `fastapi-cache2`
- **Security:** Auth0, local JWT, role-based access control (RBAC)
- **Infrastructure:** Docker, Docker Compose, `uv`, Makefile
- **Quality:** Pytest, asyncio, Ruff, Black

## Key Features

- Local email/password authentication with JWT
- Auth0 login support
- Company-based access control
- Create, publish, and manage quizzes
- Add and update questions and answers
- Quiz attempt handling
- Redis-based caching for frequently used data
- Automated cache invalidation on data changes
- Protected API endpoints with JWT authentication

## Architecture

- **Service layer:** contains business logic
- **Repository layer:** handles data persistence
- **Async design:** uses asynchronous database and API patterns
- **Caching:** Redis and `fastapi-cache2` are used to reduce repeated database work
- **Authentication:** supports both local and external identity providers

## Getting Started

### 1. Create a virtual environment

```bash
python -m venv venv
```

### 2. Activate the environment

```bash
.\venv\Scripts\activate
```

### 3. Install dependencies

```bash
uv sync
```

### 4. Configure environment variables

Copy the sample environment file and fill in the required values:

```bash
cp .env.sample .env
```

Environment files are stored in `deploy/envs`:
- `.env.dev` for development
- `.env.prod` for production

## Running the Project

### Development with Docker

```bash
make dev
```

This starts the API, PostgreSQL, and Redis containers.

### Run locally

```bash
python -m src.main
```

The API will be available at `http://localhost:8000`.

## Testing

Run the test suite with:

```bash
uv run pytest
```

## Database Migrations

Create a migration after changing SQLAlchemy models:

```bash
alembic revision --autogenerate -m "description"
```

Apply migrations:

```bash
alembic upgrade head
```

Revert the last migration:

```bash
alembic downgrade -1
```
