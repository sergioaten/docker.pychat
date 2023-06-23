FROM python:3.11.0-alpine

RUN mkdir /app
WORKDIR /app

COPY db.py .


COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt


EXPOSE 5001
CMD [ "python3", "db.py" ] 

