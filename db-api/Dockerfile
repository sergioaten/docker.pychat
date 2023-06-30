# Use the Python 3.11.0 Alpine base image
FROM python:3.11.0-alpine

# Create a directory for the application
RUN mkdir /app
WORKDIR /app

# Copy the necessary Python files
COPY db.py db.py
COPY config.py config.py
COPY encryption.py encryption.py

# Copy the requirements.txt file and install dependencies
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

# Expose port 5001
EXPOSE 5001

# Set the command to run the application
CMD [ "python3", "db.py" ]


