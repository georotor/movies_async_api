FROM python:3.10-slim

WORKDIR /opt/app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY requirements.txt requirements.txt

RUN apt-get update && apt-get install --no-install-recommends -y \
     curl \
     \
     && pip install --no-cache-dir --upgrade pip \
     && pip install --no-cache-dir -r requirements.txt \
     && pip install --no-cache-dir "gunicorn==20.1.0" "httptools==0.5.0" \
     \
     && apt autoremove -y \
     && apt-get clean \
     && rm -rf /var/lib/apt/lists/*

COPY src/ /opt/app/

RUN groupadd -r api && useradd -d /opt/app -r -g api api \
     && chown api:api -R /opt/app

USER api

ENTRYPOINT ["gunicorn", "main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000"]
