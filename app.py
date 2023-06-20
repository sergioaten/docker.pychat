# Import necessary modules
from flask import Flask, render_template, request, escape, jsonify
from flask_socketio import SocketIO, emit
from google.cloud import firestore
from google.cloud import secretmanager
import datetime
import users as u

# Create Flask app instance
app = Flask(__name__, static_url_path='/static')
app.config['SECRET_KEY'] = 'mysecretkey'
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

db = None

def get_firestone_credentials():
    # Initialize Secret Manager client
    secret_client = secretmanager.SecretManagerServiceClient()

    # Retrieve the secret value
    project_id = '1045040505707'
    secret_name = 'firestone-json'
    secret_version_name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
    response = secret_client.access_secret_version(request={"name": secret_version_name})
    secret_value = response.payload.data.decode("UTF-8")

    # Parse the secret value as JSON
    import json
    secret_data = json.loads(secret_value)

    return secret_data

def initialize_firestore():
    global db

    # Get the Firestore credentials
    secret_data = get_firestone_credentials()

    # Initialize Firestore client with the secret credentials
    db = firestore.Client.from_service_account_info(secret_data)

def upload_to_firestore(data):
    global db

    # Check if the Firestore client is initialized
    check_db_connection()

    # Use the existing Firestore client for database operations
    collection_ref = db.collection('registros')
    collection_ref.add(data)

def check_db_connection():
    global db

    # Check if the Firestore client is initialized
    if db is None:
        initialize_firestore()

def get_current_time():
    timestamp = datetime.datetime.now()
    return timestamp

def charge_all_database():
    global db
    initialize_firestore()
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
    f = open("desde_charge.txt", "w+")
    msg = "\n".join(str(message) for message in messages)
    f.write(msg)
    f.close()

    return messages  

# Create SocketIO instance and associate it with the app
socketio = SocketIO(app, async_mode='eventlet')

# Initialize empty dictionaries to store users and messages
users = {}
messages = []

# Define route for the root URL
@app.route('/')
def index():
    # Render the 'index.html' template
    return render_template('index.html')

# Event handler for client connect event
@socketio.on('connect')
def handle_connect():
    emit('chat_history', messages)
    
# Event handler for incoming message event
@socketio.on('message')
def handle_message(data):
    # Get the name of the sender from the users dictionary using the session ID
    name = users[request.sid] if request.sid in users else 'Anónimo'
    
    # Get the current time and format it
    time = get_current_time()
    time_formated = time.strftime('%m/%d-%H:%M:%S')

    # Sent the menssage data to database
    message_to_database = {'name': escape(users[request.sid]), 'message': escape(data['message']), 'date_message': time }
    upload_to_firestore(message_to_database)

    # Create a message dictionary with the sender's name and the message content
    message = {'name': escape(time_formated + " - " + users[request.sid] + "@devops:~$") if request.sid in users else 'Anónimo','message': escape(data['message'])}

    # Add the message to the messages list
    messages.append(message)
    
    # Emit the 'message' event and broadcast it to all connected clients
    emit('message', message, broadcast=True)


# Event handler for setting the user's name
@socketio.on('set_name')
def set_name(name):
    # Store the user's name in the users dictionary with the session ID as the key
    users[request.sid] = name

@app.route('/register', methods=['POST'])
def register():
    global db
    check_db_connection()

    if request.method == 'POST':
        # Handle the form submission
        name = request.form['username']  
        hash_value = request.form['hash']  
        password = request.form['password'] 

        # Check if the hash value exists in the 'secret' collection
        collection_ref = db.collection('secret')
        query = collection_ref.where('register_token', '==', hash_value)  # Query for documents where 'register_token' is equal to the provided hash
        result_hash_check = query.get()

        if len(result_hash_check) == 0:
            # No hash check found, indicating an invalid hash
            return jsonify(result='error', message='Wrong hash'), 200

        # Check if the username already exists in the 'usuarios' collection
        collection_ref = db.collection('usuarios')
        query = collection_ref.where('username', '==', name)  # Query for documents where 'username' is equal to the provided name
        result = query.get()
        
        if len(result) > 0:
            # Username already exists
            return jsonify(result='error', message='Username already exists'), 200
        else:
            hashed_password = u.hash_password(password)
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

    # Render the registration form template for GET requests
    return render_template('index.html')



# Run the app when the script is executed directly
if __name__ == '__main__':
    messages = charge_all_database()
    socketio.run(app, host='0.0.0.0', port=5000)