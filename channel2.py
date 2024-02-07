from flask import Flask, request, render_template, jsonify
import json
import requests
import datetime
import random

# Class-based application configuration
class ConfigClass(object):
    """ Flask application config """

    # Flask settings
    SECRET_KEY = 'This is an INSECURE secret!! DO NOT use this in production!!'

# Create Flask app
app = Flask(__name__)
app.config.from_object(__name__ + '.ConfigClass')  # configuration
app.app_context().push()  # create an app context before initializing db

HUB_URL = 'http://localhost:5555' # 'https://temporary-server.de'
HUB_AUTHKEY = '1234567890' # SERVER_AUTHKEY = 'Crr-K3d-2N'
CHANNEL_AUTHKEY = '22334455'
CHANNEL_NAME = 'Guessing Game'
CHANNEL_ENDPOINT = "http://localhost:5002"
CHANNEL_FILE = 'messages2.json'

WELCOME = True
NUMBER = random.randint(0,100)

@app.cli.command('register')
def register_command():
    global CHANNEL_AUTHKEY, CHANNEL_NAME, CHANNEL_ENDPOINT

    # send a POST request to server /channels
    response = requests.post(HUB_URL + '/channels', headers={'Authorization': 'authkey ' + HUB_AUTHKEY},
                             data=json.dumps({
            "name": CHANNEL_NAME,
            "endpoint": CHANNEL_ENDPOINT,
            "authkey": CHANNEL_AUTHKEY}))

    if response.status_code != 200:
        print("Error creating channel: "+str(response.status_code))
        return

def check_authorization(request):
    global CHANNEL_AUTHKEY
    # check if Authorization header is present
    if 'Authorization' not in request.headers:
        return False
    # check if authorization header is valid
    if request.headers['Authorization'] != 'authkey ' + CHANNEL_AUTHKEY:
        return False
    return True

@app.route('/health', methods=['GET'])
def health_check():
    global CHANNEL_NAME
    if not check_authorization(request):
        return "Invalid authorization", 400
    return jsonify({'name':CHANNEL_NAME}),  200

# GET: Return list of messages
@app.route('/', methods=['GET'])
def home_page():
    if not check_authorization(request):
        return "Invalid authorization", 400
    # fetch channels from server
    return jsonify(read_messages())

# POST: Send a message
@app.route('/', methods=['POST'])
def send_message():
    # fetch channels from server
    # check authorization header
    if not check_authorization(request):
        return "Invalid authorization", 400

    # check if message is present
    message = request.json
    response = respond(message)

    if not message:
        return "No message", 400
    if not 'content' in message:
        return "No content", 400
    if not 'sender' in message:
        return "No sender", 400
    if not 'timestamp' in message:
        return "No timestamp", 400
    
    # add message to messages
    messages = read_messages()
    if message['sender'] == '':
        message['sender'] = 'Player'
    messages.append({'content':message['content'], 'sender':message['sender'], 'timestamp':message['timestamp']})
    messages.append(response)
    save_messages(messages)

    return "OK", 200

def respond(message):
        global NUMBER
        time = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")

        # If user does not guess
        if not 'content' in message:
            answer = "You did not write anything. Try again."
            response = {'content':answer, 'sender':'Bot', 'timestamp':time}
            return response
        
        content = message['content']
        
        try:
            content = int(content)
            if not 0 <= content <= 100:
                answer = "You're number is not between 0 and 100. Try again."
            elif content < NUMBER:
                answer = f"{content} is too low!"
            elif content > NUMBER:
                answer = f"{content} is too high!"
            elif content == NUMBER:
                answer = f"Congratulations, you guessed my {NUMBER}! New game – guess again!."
                NUMBER = random.randint(0, 100)
            else:
                answer = "Something went wrong. Try again."
        except ValueError:
            answer = "You did not type in an integer. Try again."

        response = {'content':answer, 'sender':'Bot', 'timestamp':time}
        return response

def read_messages():
    global CHANNEL_FILE
    global WELCOME
    try:
        f = open(CHANNEL_FILE, 'r')
    except FileNotFoundError:
        return []
    try:
        messages = json.load(f)
        # append welcome message once
        if WELCOME:
            time = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")
            answer = "Welcome to the guessing game! Try to guess my number between 0 and 100."
            response = {'content':answer, 'sender':'Bot', 'timestamp':time}
            messages.append(response)
            save_messages(messages)
            WELCOME = False
    except json.decoder.JSONDecodeError:
        messages = []
    f.close()
    return messages

def save_messages(messages):
    global CHANNEL_FILE
    with open(CHANNEL_FILE, 'w') as f:
        json.dump(messages, f)

# Start development web server
if __name__ == '__main__':
    app.run(port=5002, debug=True)
