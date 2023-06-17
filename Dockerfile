FROM python:3.11.0-alpine

RUN mkdir app
WORKDIR /app

COPY static/* static/
COPY templates/* templates/
COPY *.py .
COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

EXPOSE 5000

CMD [ "python3", "app.py" ]

