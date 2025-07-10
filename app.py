from flask import Flask, request, render_template
from pymongo import MongoClient
from bson.json_util import dumps

app = Flask(__name__)

# ✅ Connect to MongoDB Atlas
client = MongoClient("mongodb+srv://Aruna_501:Sri%404788@webhook-cluster.v006jen.mongodb.net/webhook_db?retryWrites=true&w=majority&appName=webhook-cluster")
db = client.webhook_db
events_collection = db.events

@app.route('/')
def index():
    return render_template('index.html')

# ✅ Webhook endpoint
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    event_type = request.headers.get('X-GitHub-Event')
    print("🔔 Webhook received:", event_type)

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

        # ✅ Store in MongoDB
        if formatted_data:
            events_collection.insert_one(formatted_data)
            print("✅ Event saved to DB:", formatted_data)

    except Exception as e:
        print("❌ Error processing webhook:", str(e))

    return '', 200

# ✅ API to serve latest events
@app.route('/events')
def get_events():
    recent_events = events_collection.find().sort('_id', -1).limit(10)
    return dumps(recent_events)

if __name__ == '__main__':
    app.run(port=5000)
