from flask import Flask, request, render_template
from pymongo import MongoClient
from bson.json_util import dumps

app = Flask(__name__)

# Connect to MongoDB Atlas (replace with your credentials)
client = MongoClient("mongodb+srv://Aruna_501:Sri%404788@webhook-cluster.v006jen.mongodb.net/webhook_db?retryWrites=true&w=majority&appName=webhook-cluster")
db = client.webhook_db
events_collection = db.events  # Collection to store events

# Home route to display events in HTML
@app.route('/')
def index():
    return render_template('index.html')

# Route to receive GitHub webhook events
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json  # Get JSON data sent from GitHub
    event_type = request.headers.get('X-GitHub-Event')  # Get event type from header

    formatted_data = {}  # To store extracted data in simple format

    # Handle Push Event
    if event_type == "push":
        formatted_data = {
            "type": "push",
            "author": data['pusher']['name'],
            "to_branch": data['ref'].split('/')[-1],
            "timestamp": data['head_commit']['timestamp']
        }

    # Handle Pull Request (including merge)
    elif event_type == "pull_request":
        pr = data['pull_request']
        action = data['action']
        if action == "closed" and pr.get('merged'):
            formatted_data = {
                "type": "merge",
                "author": pr['user']['login'],
                "from_branch": pr['head']['ref'],
                "to_branch": pr['base']['ref'],
                "timestamp": pr['merged_at']
            }
        else:
            formatted_data = {
                "type": "pull_request",
                "author": pr['user']['login'],
                "from_branch": pr['head']['ref'],
                "to_branch": pr['base']['ref'],
                "timestamp": pr['created_at']
            }

    # Handle Pull Request Review
    elif event_type == "pull_request_review":
        formatted_data = {
            "type": "pull_request_review",
            "author": data['review']['user']['login'],
            "state": data['review']['state'],
            "timestamp": data['review']['submitted_at']
        }

    # Handle Release
    elif event_type == "release":
        formatted_data = {
            "type": "release",
            "author": data['release']['author']['login'],
            "tag": data['release']['tag_name'],
            "timestamp": data['release']['created_at']
        }

    # Handle Issues
    elif event_type == "issues":
        formatted_data = {
            "type": "issue",
            "author": data['issue']['user']['login'],
            "title": data['issue']['title'],
            "timestamp": data['issue']['created_at']
        }

    # Handle Collaborator Add/Remove
    elif event_type == "member":
        formatted_data = {
            "type": "member",
            "author": data['sender']['login'],
            "member": data['member']['login'],
            "action": data['action'],
            "timestamp": data['organization']['updated_at']
        }

    # Save to MongoDB if valid
    if formatted_data:
        events_collection.insert_one(formatted_data)

    return '', 200

# API to send recent events to frontend
@app.route('/events')
def get_events():
    recent_events = events_collection.find().sort('_id', -1).limit(10)
    return dumps(recent_events)

# Run the app
if __name__ == '__main__':
    app.run(port=5000)
