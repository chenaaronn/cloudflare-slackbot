import os
from pathlib import Path
from dotenv import load_dotenv
from urllib.parse import parse_qs
from cmd_website import handle_website
from cmd_cf import handle_cf_ray
from cmd_webby import handle_webby
from slack_sdk import WebClient

import base64
import urllib.parse

# load environment variables
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

client = WebClient(token=os.environ['SLACK_TOKEN'])

def lambda_handler(event, context):
    print("DEBUG: Raw event received:", event)

    path = event.get("rawPath", "")
    body = event.get("body", "")

    # decode base64 body if necessary
    if event.get("isBase64Encoded", False):
        body = base64.b64decode(body).decode()

    print("DEBUG: rawPath =", path)
    print("DEBUG: body =", body)

    params = parse_qs(body)
    print("DEBUG: Parsed params =", params)

    # extract slack data
    channel_id = params.get("channel_id", [""])[0]
    text = params.get("text", [""])[0]
    command = params.get("command", [""])[0].lstrip("/")
    # command = path.rsplit("/", 1)[-1] <- OLD
    print(f"DEBUG: command={command}, channel_id={channel_id}, text={text}")

    # slash command routing
    if command == "website":
        return handle_website(client, channel_id, text)
    elif command in ["cf", "cloudflare"]:
        return handle_cf_ray(client, channel_id, text)
    elif command == "webby":
        return handle_webby(client, channel_id, text) 
    elif command == "test":
        return {
            "statusCode": 200,
            "body": "Successfully running on Lambda!"
        }
    else:
        return {
            "statusCode": 400,
            "body": f"⚠️ Unknown command: `{command}`"
        }
# lambda_handler()
