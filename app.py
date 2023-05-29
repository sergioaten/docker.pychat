# Import necessary modules
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit

# Create Flask app instance
app = Flask(__name__, static_url_path='/static')
app.config['SECRET_KEY'] = 'mysecretkey'

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
    
    # Create a message dictionary with the sender's name and the message content
    message = {'name': name+"@devops:~$", 'message': data['message']}
    
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
