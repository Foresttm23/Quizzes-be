# intern-meduzzen-be

# For Deployment

## Preparation:

- ### Create a .env file inside a workdir.
- ### Fill it with sample data from `.env.sample` or use real data.

## 1. Create a container:

```bash 
docker build -t myapp .
```

## 2. Run a container:

```bash 
docker run --env-file .env -p 8000:8000 myapp
```

# For Development

## 1. Create a virtual env or use the existing one.

### 1.1 Create a venv:

```bash 
python -m venv venv
```

### 1.2 Activate a venv:

```bash 
.\venv\Scripts\activate
```

## 2. Install dependencies:

```bash 
pip install -r requirements.txt
```

## 3. Run the app:

```bash 
uvicorn app.main:app --reload
```

## 4. Run tests:

```bash 
pytest
```