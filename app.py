from flask import Flask, request, render_template, Response
from pymongo import MongoClient
from bson.json_util import dumps
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Connect to MongoDB Atlas
client = MongoClient(os.getenv("MONGO_URI"))
db = client.webhook_db
events_collection = db.events

# Home route to display events
@app.route('/')
def index():
    return render_template('index.html')

# Webhook endpoint to receive GitHub events
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    event_type = request.headers.get('X-GitHub-Event')
    formatted_data = {}

    try:
        if event_type == "push":
            formatted_data = {
                "type": "push",
                "author": data['pusher']['name'],
                "to_branch": data['ref'].split('/')[-1],
                "timestamp": data['head_commit']['timestamp']
            }

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

        elif event_type == "pull_request_review":
            formatted_data = {
                "type": "pull_request_review",
                "author": data['review']['user']['login'],
                "state": data['review']['state'],
                "timestamp": data['review']['submitted_at']
            }

        elif event_type == "release":
            formatted_data = {
                "type": "release",
                "author": data['release']['author']['login'],
                "tag": data['release']['tag_name'],
                "timestamp": data['release']['created_at']
            }

        elif event_type == "issues":
            formatted_data = {
                "type": "issue",
                "author": data['issue']['user']['login'],
                "title": data['issue']['title'],
                "timestamp": data['issue']['created_at']
            }

        elif event_type == "member":
            formatted_data = {
                "type": "member",
                "author": data['sender']['login'],
                "member": data['member']['login'],
                "action": data['action'],
                "timestamp": data['organization']['updated_at']
            }

        # Save to MongoDB
        if formatted_data:
            events_collection.insert_one(formatted_data)

    except Exception as e:
        print("Webhook Error:", e)
        return 'Error', 400

    return '', 200

# API route to send recent events to frontend
@app.route('/events')
def get_events():
    recent_events = events_collection.find().sort('_id', -1).limit(10)
    return Response(dumps(recent_events), mimetype='application/json')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
