from flask import Flask
import socket
import os

app = Flask(__name__)

@app.route('/')
def hello_world():
    print(os.system("ip a"))
    db_host = 'db-api-service'
    db_port = 5001

    ip_address = socket.gethostbyname(db_host)
    print("hola")
    print(f"The IP address of {db_host} is: {ip_address}")
    
    return f"The IP address of {db_host} is: {ip_address}"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)