###### Early reviewers: Volodymyr Tkach | Illia Puzdranovskyi | Kyrylo Lipovok

# About this project

### Technologies - FastAPI, PostgreSQL, SQLAlchemy, asyncio, Docker, JWT, Auth0, Redis, uv, pytest, alembic
#### A backend service for managing quizzes, built with FastAPI and following RESTful principles. The service separates repository and service layers and follows Domain Driven architecture to maintain clean code and scalability.

#### The platform supports both local sign-up using email and password, issuing a local JWT, as well as login via Auth0 with their JWT, both token types are supported. Each user can send companies join requests or create a company themselves by becoming its owner. Owners can send other user's invitations, manage join requests and assign roles such as admins withing the company. Users can view visible companies as well as their own companies, even if those companies are marked as invisible.

#### Company admins can create quizzes, add questions and answers, and publish quizzes for company members. Once published, questions cannot be chanaged. To update them, admin or owner should create a new version from an existing one: all questions are preserved, the new version starts unpublished, and after publishing, the previous version becomes invisible while retaining its published status. Quick change of visible quiz is also available.

#### Frequently used service calls, such as retrieving quiz attempts, are cached using Redis, the fastapi-cache2 library, and a custom decorator. Cache invalidation happens automatically on model updates using SQLAlchemy event listeners.

#### Most endpoints are protected with required JWT authentication, other with optional. (Anyone can access a list of companies, invisible companies are only visible to their members)

___

# Quizzes-be

___

## Install Docker

https://www.docker.com
___

# For IDE support and better experience configure virtual environment

### Create .venv

```bash 
python -m venv venv
```

### Activate .venv

```bash 
.\venv\Scripts\activate
```

### Install dependencies

```bash 
uv sync
```

# Project Setup

### Create local environment file.

```bash 
cp .env.sample .env
```

### Fill real or leave as is for a local development.

# Run the App

### This command will start FastApi, Postgresql and Redis in separate containers and run it in the background.

```bash 
docker compose up -d --build
```

### You can then access APi at http://localhost:8000 .

# How to Run Tests

### Tests must be run inside the running container since they need connection to the database and Redis.

```bash 
docker exec myapp uv run pytes
```

# How to Stop the Application\Containers

### To stop the containers but keep DB data

```bash 
docker compose down
```

### For full teardown\reset

```bash 
docker compose down -v
```

# For FastApi Deployment

### Create a container:

```bash 
docker build -t myapp .
```

### Run a container:

```bash 
docker run --env-file .env -p 8000:8000 myapp
```

# Creating and Applying migrations

### After you change a SQLAlchemy model  in app/db/models/ you must generate a migration script:

```bash 
alembic revision --autogenerate -m "Your message"
```

### Then to apply a migration changes:

```bash 
alembic upgrade head
```

### To revert the last changes:

```bash 
alembic downgrade -1
```
