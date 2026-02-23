# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from botbuilder.core import ActivityHandler, MessageFactory, TurnContext
from botbuilder.schema import ChannelAccount
# INSERT these imports after existing imports at the top of bots/echo_bot.py
import aiohttp
from botbuilder.schema import Attachment

from typing import List

# INSERT at module level (above class EchoBot)
def _build_user_card(u: dict) -> Attachment:
    """
    Build a clean Adaptive Card for a Beeceptor fake user object.
    """
    full_address = ", ".join(
        [p for p in [u.get("address"), u.get("state"), u.get("zip"), u.get("country")] if p]
    )
    photo_url = u.get("photo") or "https://json-server.dev/ai-profiles/1.png"

    card_json = {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.5",
        "body": [
            {
                "type": "ColumnSet",
                "columns": [
                    {
                        "type": "Column",
                        "width": "auto",
                        "items": [
                            {
                                "type": "Image",
                                "url": photo_url,
                                "size": "Medium",
                                "style": "Person"
                            }
                        ]
                    },
                    {
                        "type": "Column",
                        "width": "stretch",
                        "items": [
                            {
                                "type": "TextBlock",
                                "text": u.get("name", "Unknown"),
                                "weight": "Bolder",
                                "size": "Medium",
                                "wrap": True
                            },
                            {
                                "type": "TextBlock",
                                "text": u.get("company", ""),
                                "isSubtle": True,
                                "spacing": "None",
                                "wrap": True
                            },
                            {
                                "type": "TextBlock",
                                "text": u.get("email", ""),
                                "wrap": True
                            }
                        ]
                    }
                ]
            },
            {
                "type": "FactSet",
                "facts": [
                    {"title": "Username", "value": u.get("username", "-")},
                    {"title": "Phone", "value": u.get("phone", "-")},
                    {"title": "Address", "value": full_address or "-"}
                ]
            }
        ],
        "actions": [
            {
                "type": "Action.OpenUrl",
                "title": "Email",
                "url": f"mailto:{u.get('email', '')}"
            }
        ]
    }

    return Attachment(content_type="application/vnd.microsoft.card.adaptive", content=card_json)
class EchoBot(ActivityHandler):
    async def on_members_added_activity(
        self, members_added: List[ChannelAccount], turn_context: TurnContext
    ):
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                await turn_context.send_activity("Hello and welcome!")

    async def on_message_activity(self, turn_context: TurnContext):
        # INSERT in place of the removed echo block
        api_url = "https://fake-json-api.mock.beeceptor.com/users"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, timeout=10) as resp:
                    resp.raise_for_status()
                    payload = await resp.json()
        except Exception as ex:
            await turn_context.send_activity(f"Sorry, I couldn't fetch users right now. Error: {ex}")
            return

        # Normalize response to a list
        users = payload if isinstance(payload, list) else payload.get("users", [])
        if not users:
            await turn_context.send_activity("I didn't receive any users from the API.")
            return

        # Build cards (cap at 10 for a tidy carousel)
        attachments = [_build_user_card(u) for u in users[:10]]

        # Send as carousel (renders well in Microsoft Teams)
        message = MessageFactory.carousel(attachments, text="Here are some users I found:")
        await turn_context.send_activity(message)

