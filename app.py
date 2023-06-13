# Import necessary modules
from flask import Flask, render_template, request, escape
from flask_socketio import SocketIO, emit
from google.cloud import firestore
from google.cloud import secretmanager
import datetime
# Create Flask app instance
app = Flask(__name__, static_url_path='/static')
app.config['SECRET_KEY'] = 'mysecretkey'
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

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
    
    print(timestamp)
    for doc in documents:
        data = doc.to_dict()
        name = data['name']
        message = data['message']
        print(f'Name: {name}, Message: {message}')

def get_current_time():
    timestamp = datetime.datetime.now()
    return timestamp

def upload_to_firestore(data):
    # Get the Firestore credentials
    secret_data = get_firestone_credentials()

    # Initialize Firestore client with the secret credentials
    db = firestore.Client.from_service_account_info(secret_data)

    # Create a document in the "registros" collection with the name, message, and date_message
    collection_ref = db.collection('registros')
    collection_ref.add(data)

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
    # Emit the 'chat_history' event and send the list of messages to the client
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

# Run the app when the script is executed directly
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
