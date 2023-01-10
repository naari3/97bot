FROM python:3.11.1

RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg \
    && apt-get -y clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY Pipfile /app/Pipfile
COPY Pipfile.lock /app/Pipfile.lock
RUN pip install pipenv
RUN pipenv sync

COPY . /app

ENTRYPOINT ["pipenv", "run", "python", "main.py"]
