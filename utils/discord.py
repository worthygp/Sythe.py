import json
import requests


class Webhook:
    def __init__(
        self, url: str, type: int, message_id: int,
        channel_id: int, webhook_id: int,
        timestamp: str, embeds: list = []
    ):
        self.url = url
        self.type = type
        self.message_id = message_id
        self.channel_id = channel_id
        self.webhook_id = webhook_id
        self.timestamp = timestamp
        self.embeds = embeds

    def edit(self, content: str, embeds: list = []):
        """ Edit a message to the webhook """
        embeds = embeds or self.embeds

        if not embeds and not content:
            raise Exception("Either embed or content must be defined")

        r = requests.patch(
            f"{self.url}/messages/{self.message_id}",
            headers={"Content-Type": "application/json"},
            data=json.dumps({
                "content": content,
                "embeds": embeds
            })
        )

        if r.status_code != 200:
            raise Exception(f"Failed to edit message: {r.text}")

        return r

    def delete(self):
        """ Delete a webhook message """
        r = requests.delete(
            f"{self.url}/messages/{self.message_id}",
            headers={"Content-Type": "application/json"}
        )

        return r
