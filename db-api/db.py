from google.cloud import firestore
from google.cloud import secretmanager
from google.api_core.exceptions import GoogleAPIError
from flask import Flask, jsonify, request
import json
import os

FS_MESG_COLLECTION = 'registros'
FS_USERS_COLLECTION = 'usuarios'

app = Flask(__name__)

def initialize_firestore():
    try:
        # Get the Firestore credentials
        secret_data = get_firestore_credentials()

        # Initialize Firestore client with the secret credentials
        global db
        db = firestore.Client.from_service_account_info(secret_data)
        print("Firestore client initialized successfully")
    except (GoogleAPIError) as e:
        # Handle initialization errors
        print("Failed to initialize Firestore client:", str(e))

def get_firestore_credentials():
    # Retrieve the secret value
    project_id = '1045040505707'
    secret_name = 'firestone-json'
    secret_version_name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
    secret_client = secretmanager.SecretManagerServiceClient()
    response = secret_client.access_secret_version(request={"name": secret_version_name})
    secret_value = response.payload.data.decode("UTF-8")

    # Parse the secret value as JSON
    secret_data = json.loads(secret_value)

    return secret_data

@app.route('/charge', methods=['GET'])
def charge_all_database():
    try:
        collection_ref = db.collection('registros')
        query = collection_ref.order_by('date_message', direction=firestore.Query.ASCENDING)
        documents = query.get()

        # Prepare the list of messages
        messages = []
        for doc in documents:
            data = doc.to_dict()
            name = data['name']
            msg = data['message']
            time = data['date_message'].strftime('%m/%d-%H:%M:%S')  # Convert to string
            message = {'name': time + " - " + name + "@devops:~$", 'message': msg}
            messages.append(message)

        return jsonify(messages)
    except GoogleAPIError as e:
        # Handle Firestore query errors
        return jsonify(error=str(e)), 500

@app.route('/upload', methods=['POST'])
def upload_to_firestore():
    global db

    # Check if the Firestore client is initialized
    check_db_connection()

    # Get the data from the request body
    data = request.get_json()

    # Use the existing Firestore client for database operations
    collection_ref = db.collection(FS_MESG_COLLECTION)
    collection_ref.add(data)

    return jsonify({'message': 'Data uploaded successfully'})

def check_db_connection():
    global db

    # Check if the Firestore client is initialized
    if db is None:
        initialize_firestore()

@app.route('/secret', methods=['POST'])
def check_secret():
    initialize_firestore()

    # Get the hash value from the request
    hash_value = request.json.get('hash_value')

    # Check if the hash value exists in the 'secret' collection
    secret_collection = db.collection('secret')
    query = secret_collection.where('register_token', '==', hash_value)
    result = query.get()

    if len(result) == 0:
        # Hash not found, indicating an invalid hash
        return jsonify(result='error', message='Wrong hash'), 200
    else:
        # Hash found, indicating a valid hash
        return jsonify(result='success', message='Valid hash'), 200

@app.route('/users', methods=['POST'])
def check_username():
    initialize_firestore()

    # Get the username from the request
    username = request.json.get('username')

    # Check if the username exists in the 'usuarios' collection
    users_collection = db.collection('usuarios')
    query = users_collection.where('username', '==', username)
    result = query.get()

    if len(result) > 0:
        # Username already exists
        return jsonify(result='error', message='Username already exists'), 200
    else:
        # Username does not exist
        return jsonify(result='success', message='Username available'), 200

@app.route('/register', methods=['POST'])
def register_user():
    initialize_firestore()

    # Get the user data from the request
    user_data = request.json

    # Add the new user to the 'usuarios' collection
    users_collection = db.collection('usuarios')
    doc_ref = users_collection.document()
    doc_ref.set(user_data)

    return jsonify(result='success', message='Registration successful'), 200

if __name__ == '__main__':
    # Initialize Firestore client during application startup
    print(os.system("ip a"))
    initialize_firestore()
    app.run(host='0.0.0.0', port=5001)
