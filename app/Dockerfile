# Use the Python 3.11.0 Alpine base image
FROM python:3.11.0-alpine

# Create a directory for the application
RUN mkdir /app
WORKDIR /app

# Copy static and templates directories
COPY static/ static/
COPY templates/ templates/

# Copy the Python application files
COPY app.py app.py

# Copy the requirements.txt file and install dependencies
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

# Expose port 5000
EXPOSE 5000

# Set the command to run the application
CMD [ "python3", "app.py" ]

