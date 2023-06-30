# Pychat
## Chat Application with Flask and Firestore Database

This chat application is built using Flask, Socket.IO, and Firestore database. It allows users to chat in real-time and saves the messages in a Firestore database. The application can be run in a local environment using cloud code or deployed in a Kubernetes cluster (GKE) using the provided Kubernetes manifest.

## Features
* Real-time chat using Socket.IO: Users can send and receive messages in real-time.
* Firestore database: Messages are stored in a Firestore database for persistence and retrieval.
* Microservices architecture: The application is split into two microservices: PyChat and DB.
* PyChat microservice: Handles the chat functionality, communicates with the front-end using Socket.IO, and sends messages to the DB microservice.
* DB microservice: Responsible for interacting with the Firestore database, receives messages from the PyChat microservice, and saves them in the database.