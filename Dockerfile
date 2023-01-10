FROM python:3.11.1

RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg \
    && apt-get -y clean && rm -rf /var/lib/apt/lists/*

COPY . /app
WORKDIR /app
RUN pip install pipenv

RUN pipenv sync

ENTRYPOINT ["pipenv", "run", "python", "main.py"]
