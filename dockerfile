FROM python:slim

WORKDIR /app

COPY src/requirements.txt .

RUN pip install -r requirements.txt

COPY src/quake.py .
COPY src/last.txt .


ENTRYPOINT [ "python", "quake.py" ]