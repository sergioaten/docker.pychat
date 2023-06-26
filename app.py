# Import necessary modules
from flask import Flask, render_template, request, escape, jsonify
from flask_socketio import SocketIO, emit
import datetime
import users as u
import requests
import os
import time

# Create Flask app instance
app = Flask(__name__, static_url_path='/static')
app.config['SECRET_KEY'] = 'mysecretkey'
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

first_run = True

db_host = 'db-api-service'
db_port = 5001
db_endpoint = f"http://{db_host}:{db_port}"

def charge_all_messages():
    charge_api = f"{db_endpoint}/charge"
    response = requests.get(charge_api)
    if response.status_code == 200:
        result = response.json()
        #result_strings = [data['name'] + data['message'] for data in result]
        #messages = '\n'.join(result_strings)

        for data in result:
            messages.append(data['name'] + data['message'])

        #with open("output.txt", 'w+') as out:
        #    result = [data['name'] + data['message'] for data in messages]
        #    message_string = '\n'.join(result)
        #    out.write(message_string)
        #with open("output.txt", 'w+') as out:
        #    out.write(messages)
        return messages
        # Process the messages data as needed
    else:
        print('Failed to retrieve messages:', response.status_code)


def get_current_time():
    timestamp = datetime.datetime.now()
    return timestamp

# Create SocketIO instance and associate it with the app
socketio = SocketIO(app, async_mode='eventlet')

# Initialize empty dictionaries to store users and messages
users = {}
messages = []


# Define route for the root URL
@app.route('/')
def index():
    global first_run  # Use the 'global' keyword to modify the global variable
    global messages
    if first_run:
        messages = charge_all_messages()
        first_run = False
    # Render the 'index.html' template
    return render_template('index.html')

# Event handler for client connect event
@socketio.on('connect')
def handle_connect():
    emit('chat_history', messages)

# Event handler for incoming message event
@socketio.on('message')
def handle_message(data):
    # Get the current time and format it
    time = get_current_time()
    time_formatted = time.strftime('%m/%d-%H:%M:%S')

    # Send the message data to the database
    message_to_database = {'name': escape(users[request.sid]), 'message': escape(data['message']), 'date_message': time}
    upload_to_firestore(message_to_database)

    # Create a message dictionary with the sender's name and the message content
    message = {'name': escape(time_formatted + " - " + users[request.sid] + "@devops:~$") if request.sid in users else 'Anónimo', 'message': escape(data['message'])}

    # Add the message to the messages list
    messages.append(message)

    # Emit the 'message' event and broadcast it to all connected clients
    emit('message', message, broadcast=True)

# Event handler for setting the user's name
@socketio.on('set_name')
def set_name(name):
    # Store the user's name in the users dictionary with the session ID as the key
    users[request.sid] = name

@app.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
        # Handle the form submission
        #messages = charge_all_messages()
        name = request.form['username']
        password = request.form['password']

        # Make a request to the user and hash check API endpoint
        api_endpoint = f"{db_endpoint}/check_username"
        login_payload = {
            'username': name,
            'password': password
        }
        response = requests.post(api_endpoint, data=login_payload)

        if response.status_code == 200:
            result = response.json()
            return jsonify(result), 200
        else:
            return jsonify(result='error', message='Failed to process login'), 500

    # Return an error response for unsupported request methods
    return jsonify(result='error', message='Invalid request method'), 405


@app.route('/register', methods=['POST'])
def register():
    if request.method == 'POST':
        # Handle the form submission
        name = request.form['username']
        hash_value = request.form['hash']
        password = request.form['password']

        register_payload = {
            'username': name,
            'hash_value': hash_value,
            'password': password
        }

        # Make a request to the db-api for registration
        register_api = f"{db_endpoint}/register"
        response = requests.post(register_api, data=register_payload)

        if response.status_code == 200:
            result = response.json()
            return jsonify(result), 200
        else:
            return jsonify(result='error', message='Failed to register'), 500


# Run the app when the script is executed directly
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)