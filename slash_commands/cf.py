# /cf -ray [ray ID] or /cloudflare -ray [ray ID]
from flask import request, Response
import re

# ray IDs format: 16-character alphanumeric strings; case-insensitive 
# example: "783dd7324ebfbb62"
RAY_ID_REGEX = re.compile(r"^[a-fA-F0-9]{16}$")

def handle_cf_ray(client):
    data = request.form
    channel_id = data.get('channel_id')
    text = data.get('text')

    args = text.strip().split()

    # check if user provided exactly 2 args: -ray and [ray_id]
    if len(args) != 2 or args[0] != "-ray":
        return Response("Usage: /cf -ray [ray_id] or /cloudflare -ray [ray_id]", status=200)

    ray_id = args[1]

    # validate Ray ID format
    if not RAY_ID_REGEX.fullmatch(ray_id):
        return Response("Invalid Ray ID format. A Ray ID is a 16-character hex string (e.g., 783dd7324ebfbb62).", status=200)

    response_msg = (
        f"*Ray ID:* {ray_id}\n"
        f"*Service:* \n"
        f"*Action Taken:* "
    )

    client.chat_postMessage(channel=channel_id, text=response_msg)
    return Response(), 200
# handle_cf_ray()