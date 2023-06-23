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
    #initialize_firestore()
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
    initialize_firestore()

    # Get the user data from the request
    user_data = request.json

    # Add the new user to the 'usuarios' collection
    users_collection = db.collection('usuarios')
    doc_ref = users_collection.document()
    doc_ref.set(user_data)

    return jsonify(result='success', message='Registration successful'), 200

def hash_password(password):
    # Generate a salt
    salt = bcrypt.gensalt()

    # Hash the password
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)

    # Return the hashed password as a string
    return hashed_password.decode('utf-8')

def verify_password(password, hashed_password):
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

if __name__ == '__main__':
    # Initialize Firestore client during application startup
    print(os.system("ip a"))
    initialize_firestore()
    app.run(host='0.0.0.0', port=5001)
