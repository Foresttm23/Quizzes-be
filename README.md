# intern-meduzzen-be

## 1. To start the application create a virtual env or use the existing one.
- ### To create and activate a venv:
  - ```bash 
    python -m venv venv
    
    .\venv\Scripts\activate
    ```

## 2. In the project dir execute command: 
```bash 
pip install -r requirements.txt
```

## 3. To run the app execute command:
```bash 
uvicorn app.main:app --reload
```

## 4. For tests in the project directory execute:
```bash 
pytest
```