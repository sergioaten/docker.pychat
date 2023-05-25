from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mysecretkey'
socketio = SocketIO(app, async_mode='eventlet')

users = {}
messages = []

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    emit('chat_history', messages)

@socketio.on('message')
def handle_message(data):
    name = users[request.sid] if request.sid in users else 'Anónimo'
    message = {'name': name, 'message': data['message']}
    messages.append(message)
    emit('message', message, broadcast=True)

@socketio.on('set_name')
def set_name(name):
    users[request.sid] = name

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug="TRUE")
