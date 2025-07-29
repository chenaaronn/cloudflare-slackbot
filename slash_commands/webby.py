from flask import request, Response
import random

from flask import request, Response
import random

def handle_webby(client):
    data = request.form
    channel_id = data.get('channel_id')
    text = data.get('text', '').strip().lower()

    if text == 'flip':
        result = random.choice(['Heads', 'Tails'])
        client.chat_postMessage(channel=channel_id, text=f"🪙 You flipped *{result}*!")
    
    elif text.startswith('roll'):
        try:
            parts = text.split()
            if len(parts) == 1:
                sides = 6
            elif parts[1].startswith('d') and parts[1][1:].isdigit():
                sides = int(parts[1][1:])
            else:
                raise ValueError("Invalid format")
            
            result = random.randint(1, sides)
            client.chat_postMessage(channel=channel_id, text=f"🎲 You rolled a *{result}* (1–{sides})")
        except Exception:
            client.chat_postMessage(channel=channel_id, text="❗ Invalid roll format. Use `/webby roll` or `/webby roll d(number of sides)`.")

    elif text == '' or text == 'help':
        return handle_webby_help(client)
    else:
        client.chat_postMessage(
            channel=channel_id,
            text=f"❓ Sorry, I don't recognize that command. Type `/webby` or `/webby help` to see what I can do."
        )

    return Response(), 200
# handle_webby()
from flask import request, Response

def handle_webby_help(client):
    data = request.form
    channel_id = data.get('channel_id')

    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "Hi! I'm *Webby* – your Cloudflare & web tools assistant.\n\nHere are the commands I support:"
            }
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*`/cf -ray [ray_id]`* or *`/cloudflare -ray [ray_id]`*\nLook up Cloudflare Firewall Events for a specific Ray ID.\n\n*Example:* `/cf -ray 783dd7324ebfbb62`"
            }
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "_Ray IDs must be tied to firewall/security events to return data, and there may be a short delay (up to 1 minute) after an event is logged._"
                }
            ]
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*`/website [website_url]`*\nCheck hosting, IP ownership, and DNS records for a domain.\n\n*Example:* `/website deepblue.lib.umich.edu`"
            }
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "Need help? Just type *`/webby`* or *`/help`* anytime."
            }
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "_Built by U-M ITS Web Hosting._"
                }
            ]
        }
    ]

    client.chat_postMessage(channel=channel_id, blocks=blocks)
    return Response(), 200

