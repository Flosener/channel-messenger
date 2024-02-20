from flask import Flask, request, render_template, jsonify
import json
import requests
import datetime
import random
import os
import nltk
from nltk.tokenize import word_tokenize
from collections import Counter
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
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
CHANNEL_NAME = 'ChatBot for CogSci'
CHANNEL_ENDPOINT = "http://localhost:5002"
CHANNEL_FILE = 'messages2.json'

WELCOME = True
NUMBER = random.randint(0,100)

with open('intents.json',encoding='utf-8') as file:
    intents = json.load(file)
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
        message['sender'] = 'You'
    messages.append({'content':message['content'], 'sender':message['sender'], 'timestamp':message['timestamp']})
    messages.append(response)
    save_messages(messages)

    return "OK", 200
def get_response(tag):
    for intent in intents['intents']:
        if intent['tag'] == tag:
            return random.choice(intent['responses'])
def get_intent_tag(message):
    # Tokenize the message
    tokens = word_tokenize(message)
    # Initialize intent tag
    intent_tags =[]
    matching_patterns = []
    for intent in intents['intents']:
        for pattern in intent['patterns']:
            if all(word in pattern for word in tokens):
                matching_patterns.append((intent['tag'], pattern))

    if matching_patterns:
        # Sort patterns by length to prioritize patterns with all words
        matching_patterns.sort(key=lambda x: len(x[1]))
        tag, pattern = matching_patterns[0]  # Get the first (shortest) matching pattern
        print(f"Found matching pattern: {pattern} for intent tag: {tag}")
        return tag
# Function to respond to user messages based on the recognized intent tag
def respond(message):
    # Get the intent tag from the message
    tag = get_intent_tag(message['content'])
    print(f" this is {tag}")
    # If intent tag is found, get a response based on the tag
    if tag:
        return {'content': get_response(tag), 'sender': 'Bot'}
    else:
       most_common_tag = get_most_common_tag(message['content'])
       if most_common_tag:
            response = f"I'm not sure what you mean, but I think '{most_common_tag}' is relevant for you. <br>"+get_response(most_common_tag)
            return {'content': response, 'sender': 'Bot', 'tag': most_common_tag}
       
       else:
            return {'content': "Sorry, nothing was found.", 'sender': 'Bot'}


def get_most_common_tag(message):
    # Tokenize the message
    tokens = word_tokenize(message)
    # Initialize intent tag list
    intent_tags = []
    # Check for intent tags in the tagged tokens
    for word in tokens:
        # Check if the word is present in any intent pattern
        for intent in intents['intents']:
            for pattern in intent['patterns']:
                if word in pattern:
                    intent_tags.append(intent['tag']) 
        
    # Count the occurrences of each tag
    tag_counts = Counter(intent_tags)
    if intent_tags:
        # Get the most common tag
        most_common_tag, _ = tag_counts.most_common(1)[0]
        return most_common_tag
    else:
        return None
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
            answer = get_response('greeting')
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
