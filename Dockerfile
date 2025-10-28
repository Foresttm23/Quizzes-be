FROM python:3.13-slim

# More clean and better for debug
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /package

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt
# Since I cant execute it on Windows
COPY start.sh .
RUN chmod +x start.sh

# Since we want to reload container with the code we dont "Copy" but import local /app folder to the container
# COPY ./app /package/app

EXPOSE 8000

ENTRYPOINT ["/package/start.sh"]