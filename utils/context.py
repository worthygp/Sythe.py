import requests
import json

from utils.discord import Webhook


class Context:
    def __init__(self, token_url: str):
        self.token_url = token_url

    def send(self, content: str, embeds: dict = None):
        """ Send a message to the webhook """
        data = {"content": content}
        if embeds:
            data["embeds"] = [embeds]

        r = requests.post(
            f"{self.token_url}?wait=true",
            headers={"Content-Type": "application/json"},
            data=json.dumps(data)
        )

        if r.status_code != 200:
            raise Exception(f"Failed to send message: {r.text}")

        data = r.json()

        return Webhook(
            self.token_url, data["type"],
            int(data["id"]), int(data["channel_id"]),
            int(data["webhook_id"]), data["timestamp"],
            data["embeds"]
        )
