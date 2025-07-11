# mattermost_notifier.py
import requests
import os
from dotenv import load_dotenv

load_dotenv()

MATTERMOST_URL = os.getenv("MATTERMOST_URL")
MATTERMOST_TOKEN = os.getenv("MATTERMOST_TOKEN")
MATTERMOST_TEAM_NAME = os.getenv("MATTERMOST_TEAM_NAME")

def log(message, level="INFO"):
    print(f"[MattermostNotifier][{level}] {message}")

def _get_channel_id(channel_name: str) -> str | None:
    headers = {
        "Authorization": f"Bearer {MATTERMOST_TOKEN}"
    }

    try:
        team_resp = requests.get(
            f"{MATTERMOST_URL}/teams/name/{MATTERMOST_TEAM_NAME}",
            headers=headers,
            timeout=5
        )
        if team_resp.status_code != 200:
            log(f"Failed to get team ID: {team_resp.text}", "ERROR")
            return None
        team_id = team_resp.json().get("id")

        channel_resp = requests.get(
            f"{MATTERMOST_URL}/teams/{team_id}/channels/name/{channel_name}",
            headers=headers,
            timeout=5
        )
        if channel_resp.status_code == 200:
            return channel_resp.json().get("id")
        else:
            log(f"Failed to get channel ID: {channel_resp.text}", "ERROR")
    except requests.exceptions.RequestException as e:
        log(f"Request error while fetching channel ID: {e}", "ERROR")

    return None

def send_message(channel_name: str, message: str):
    """Send a message to a Mattermost channel by name"""
    channel_id = _get_channel_id(channel_name)
    if not channel_id:
        log(f"Channel '{channel_name}' not found. Message not sent.", "ERROR")
        return

    headers = {
        "Authorization": f"Bearer {MATTERMOST_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "channel_id": channel_id,
        "message": message
    }

    try:
        response = requests.post(
            f"{MATTERMOST_URL}/posts",
            headers=headers,
            json=payload,
            timeout=10
        )
        if response.status_code != 201:
            log(f"Failed to send message: {response.status_code}, {response.text}", "ERROR")
        else:
            log(f"Message sent to Mattermost channel '{channel_name}'", "INFO")
    except requests.exceptions.RequestException as e:
        log(f"Request error while sending message: {e}", "ERROR")
