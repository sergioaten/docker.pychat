from google.cloud import firestore
from google.cloud import secretmanager
from google.api_core.exceptions import GoogleAPIError
from flask import Flask, jsonify, request
import json
import os
import config as conf
from datetime import datetime, timedelta
import encryption as enc


app = Flask(__name__)

db = None

def get_current_time():
    server_time = firestore.SERVER_TIMESTAMP
    return server_time

def format_time(time):
    date_str, time_str = time.split('-')

    # Extract the hours component from the time string
    hours_str = time_str.split(':')[0]
    hours = int(hours_str)

    # Add 2 hours to the hours component
    hours += 2

    # Adjust the hours if needed
    if hours >= 24:
        hours -= 24

    # Update the hours component in the time string
    hours_str = str(hours).zfill(2)
    adjusted_time_str = hours_str + ':' + ':'.join(time_str.split(':')[1:])

    # Combine the adjusted date and time components
    adjusted_time = date_str + '-' + adjusted_time_str
    return adjusted_time

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

@app.route('/charge', methods=['GET'])
def charge_all_messages():
    if request.method == 'GET':
        check_db_connection()
        collection_ref = db.collection(conf.FS_MESG_COLLECTION)
        query = collection_ref.order_by('date_message', direction=firestore.Query.ASCENDING)
        documents = query.get()

        # Prepare the list of messages
        messages = []
    for doc in documents:
        data = doc.to_dict()
        name = data['name']
        msg = data['message']
        try:
            # Format the adjusted timestamp

            time = data['date_message'].strftime('%m/%d-%H:%M:%S')  # Convert to string
            formated_time = format_time(time)
            #time = data['date_message']  # Convert to string
            if name == "Tg":
                with open("out.txt", 'w+') as out:
                    out.write(formated_time)
            message = {'name': formated_time + " - " + name + "@devops:~$", 'message': msg}
            messages.append(message)
        except AttributeError:
            print("Bad time format")
    return messages 

# API endpoint for uploading data to Firestore
@app.route('/upload', methods=['POST'])
def upload_to_firestore():
    check_db_connection()

    # Get the data from the request form
    name = request.form['name']
    message = request.form['message']
    #date_message = request.form['date_message']
    server_time = get_current_time()
    # Create a dictionary to store the message data
    data = {
        'name': name,
        'message': message,
        'date_message': server_time
    }

    # Use the existing Firestore client for database operations
    collection_ref = db.collection(conf.FS_MESG_COLLECTION)
    collection_ref.add(data)

    # Return a response or appropriate status code if needed
    return "Data uploaded successfully"


@app.route('/check_username', methods=['POST'])
def check_user_and_hash():
    check_db_connection()

    if request.method == 'POST':
        # Handle the form submission
        name = request.form['username']
        password = request.form['password']

        # Check if the username exists in the 'usuarios' collection
        collection_ref = db.collection(conf.FS_USERS_COLLECTION)
        query = collection_ref.where('username', '==', name)  # Query for documents where 'username' is equal to the provided name
        result = query.get()

        if len(result) == 0:
            # Username doesn't exist
            return jsonify(result='error', message='Invalid credentials'), 200
        else:
            user_data = result[0].to_dict()
            hashed_password = user_data.get('password')

            if enc.verify_password(password, hashed_password):
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
    collection_ref = db.collection(conf.FS_USERS_COLLECTION)
    query = collection_ref.where('username', '==', name).limit(1)
    result = query.get()

    if result:
        # Username already exists
        return jsonify(result='error', message='Username already exists'), 200
    else:
        hashed_password = enc.hash_password(password)
        # Get the server time
        server_time = get_current_time()
        # Create a new user document with the provided username and password
        new_user = {
            'username': name,
            'password': hashed_password,
            'register_date': server_time
        }
        collection_ref.add(new_user)  # Add the new user document to the 'usuarios' collection
        return jsonify(result='create', message='Registration successful'), 200

   

@app.route('/hello', methods=['GET'])
def hello():
    return jsonify(message='Hello')

if __name__ == '__main__':
    check_db_connection()
    app.run(host='0.0.0.0', port=5001)