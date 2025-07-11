# main Slack bot logic + event handlers
import os
from pathlib import Path

import slack
from flask import Flask, request, Response
from dotenv import load_dotenv
from slackeventsapi import SlackEventAdapter

from slash_commands.website import handle_website
from slash_commands.cf import handle_cf_ray

# loads environment variables
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

# launches a web server to handle incoming HTTP requests (required for Slack Events API)
# current running webserver
app = Flask(__name__) 

# connects Slack to your Flask app via the Events API.
# slack sends events (ie msgs) to your /slack/events endpoint
slack_event_adapter = SlackEventAdapter(os.environ['SIGNING_SECRET'],'/slack/events', app)

# gives bot the ability to send messages, fetch users, channels, etc.
# uses the Slack Web API
client = slack.WebClient(token=os.environ['SLACK_TOKEN'])
# return bot id
BOT_ID = client.api_call("auth.test")['user_id']

# EVENT HANDLING TUT EXAMPLE
@slack_event_adapter.on('message')
def handle_message(event_data):
    event = event_data.get('event', {}) # look for event, if nothing return blank dict; this is bascially msg
    channel_id = event.get('channel')
    user_id = event.get('user')
    text = event.get('text')
    
    if BOT_ID != user_id:
        if 'hi webby' in text.lower() or 'hello webby' in text.lower():
            client.chat_postMessage(channel=channel_id, text=f"Hello <@{user_id}>!")
        elif 'echo' in text.lower():
            client.chat_postMessage(channel=channel_id, text=text)
    
@app.route('/website', methods=['POST'])
def website():
    return handle_website(client)

@app.route('/cf', methods=['POST'])
@app.route('/cloudflare', methods=['POST'])
def cloudflare_command():
    return handle_cf_ray(client) 

# automatically update the web server
if __name__ == "__main__":
    app.run(debug=True)
