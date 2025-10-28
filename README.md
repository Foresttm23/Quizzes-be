# intern-meduzzen-be

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
pip install -r requirements.txt
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
docker exec -it myapp pytest
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