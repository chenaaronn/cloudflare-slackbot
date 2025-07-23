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
                "text": "*`/website [website_url]`*\nCheck hosting, IP ownership, and DNS records for a domain.\n\n*Example:* `/website giving.umich.edu`"
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
