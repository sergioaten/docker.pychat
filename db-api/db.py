from google.cloud import firestore
from google.cloud import secretmanager
from google.api_core.exceptions import GoogleAPIError
from flask import Flask, jsonify, request
import json
import os
import bcrypt

FS_MESG_COLLECTION = 'registros'
FS_USERS_COLLECTION = 'usuarios'

app = Flask(__name__)

db = None

def check_db_connection():
    global db

    # Check if the Firestore client is initialized
    if db is None:
        initialize_firestore()

def initialize_firestore():
    try:
        # Get the Firestore credentials
        secret_data = get_firestore_credentials()

        # Initialize Firestore client with the secret credentials
        global db
        db = firestore.Client.from_service_account_info(secret_data)
        print("Firestore client initialized successfully")
    except GoogleAPIError as e:
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

@app.route('/check_username', methods=['POST'])
def check_user_and_hash():
    check_db_connection()

    if request.method == 'POST':
        # Handle the form submission
        name = request.form['username']
        password = request.form['password']

        # Check if the username exists in the 'usuarios' collection
        collection_ref = db.collection(FS_USERS_COLLECTION)
        query = collection_ref.where('username', '==', name)  # Query for documents where 'username' is equal to the provided name
        result = query.get()

        if len(result) == 0:
            # Username doesn't exist
            return jsonify(result='error', message='Invalid credentials'), 200
        else:
            user_data = result[0].to_dict()
            hashed_password = user_data.get('password')

            if verify_password(password, hashed_password):
                # Login successful
                return jsonify(result='success', message='Login successful'), 200
            else:
                # Invalid password
                return jsonify(result='error', message='Invalid credentials'), 200

    # Return an error response for unsupported request methods
    return jsonify(result='error', message='Invalid request method'), 405

@app.route('/register', methods=['POST'])
def register_user():
    check_db_connection()

    # Get the user data from the request
    name = request.form['username']
    hash_value = request.form['hash_value']
    password = request.form['password']


    # Check the hash
    collection_ref = db.collection('secret')
    query = collection_ref.where('register_token', '==', hash_value).limit(1)
    result_hash_check = query.get()

    if not result_hash_check:
        # No hash check found, indicating an invalid hash
        return jsonify(result='error', message='Wrong hash'), 200

    # Check if the username already exists in the 'usuarios' collection
    collection_ref = db.collection(FS_USERS_COLLECTION)
    query = collection_ref.where('username', '==', name).limit(1)
    result = query.get()

    if result:
        # Username already exists
        return jsonify(result='error', message='Username already exists'), 200
    else:
        hashed_password = hash_password(password)
        # Get the server time
        server_time = firestore.SERVER_TIMESTAMP
        # Create a new user document with the provided username and password
        new_user = {
            'username': name,
            'password': hashed_password,
            'register_date': server_time
        }
        collection_ref.add(new_user)  # Add the new user document to the 'usuarios' collection
        return jsonify(result='create', message='Registration successful'), 200

   

def hash_password(password):
    # Generate a salt
    salt = bcrypt.gensalt()

    # Hash the password
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)

    # Return the hashed password as a string
    return hashed_password.decode('utf-8')

def verify_password(password, hashed_password):
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

@app.route('/hello', methods=['GET'])
def hello():
    return jsonify(message='Hello')

if __name__ == '__main__':
    check_db_connection()
    app.run(host='0.0.0.0', port=5001)
