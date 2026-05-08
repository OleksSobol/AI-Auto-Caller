"""
Push Notification Service
Sends FCM push notifications to the Flutter app for key events:
  - Incoming call auto-answered
  - Scambaiter campaign started / stopped
  - Scambaiter time-wasted milestone (every 10 minutes)
  - New call recording ready
"""

import os
import json
import asyncio
import aiohttp
from typing import Optional, List
from dotenv import load_dotenv

load_dotenv()

FCM_URL = "https://fcm.googleapis.com/fcm/send"


class NotificationService:
    """Firebase Cloud Messaging push notification sender"""

    def __init__(self):
        self.fcm_server_key = os.getenv("FCM_SERVER_KEY")
        self._device_tokens: List[str] = []
        self._load_tokens()

    # ------------------------------------------------------------------ #
    # Token management                                                     #
    # ------------------------------------------------------------------ #

    def _tokens_file(self):
        from pathlib import Path
        return Path(__file__).parent / "fcm_tokens.json"

    def _load_tokens(self):
        f = self._tokens_file()
        if f.exists():
            with open(f) as fp:
                self._device_tokens = json.load(fp)

    def _save_tokens(self):
        with open(self._tokens_file(), "w") as f:
            json.dump(self._device_tokens, f)

    def register_token(self, token: str):
        """Register a device FCM token (called when app starts)."""
        if token not in self._device_tokens:
            self._device_tokens.append(token)
            self._save_tokens()

    def unregister_token(self, token: str):
        self._device_tokens = [t for t in self._device_tokens if t != token]
        self._save_tokens()

    # ------------------------------------------------------------------ #
    # Send helpers                                                         #
    # ------------------------------------------------------------------ #

    async def send(self, title: str, body: str,
                   data: Optional[dict] = None) -> bool:
        """
        Send a push notification to all registered devices.

        Returns True if at least one notification was delivered.
        """
        if not self._device_tokens:
            # No devices registered — log and continue
            print(f"[NOTIFY] {title}: {body} (no devices registered)")
            return False

        if not self.fcm_server_key:
            print(f"[NOTIFY] FCM key not set. Would send: {title} — {body}")
            return False

        payload = {
            "registration_ids": self._device_tokens,
            "notification": {"title": title, "body": body, "sound": "default"},
            "data": data or {},
            "priority": "high",
        }
        headers = {
            "Authorization": f"key={self.fcm_server_key}",
            "Content-Type": "application/json",
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(FCM_URL, json=payload,
                                        headers=headers, timeout=10) as r:
                    resp = await r.json()
                    success = resp.get("success", 0) > 0
                    if not success:
                        print(f"[NOTIFY] FCM error: {resp}")
                    return success
        except Exception as e:
            print(f"[NOTIFY] Send failed: {e}")
            return False

    # ------------------------------------------------------------------ #
    # Convenience notification events                                      #
    # ------------------------------------------------------------------ #

    async def notify_call_answered(self, caller_number: str, call_id: str):
        await self.send(
            title="📞 Call Auto-Answered",
            body=f"Incoming call from {caller_number} was answered by AI.",
            data={"event": "call_answered", "call_id": call_id,
                  "caller": caller_number},
        )

    async def notify_call_ended(self, caller_number: str,
                                duration_seconds: float):
        mins = int(duration_seconds // 60)
        secs = int(duration_seconds % 60)
        await self.send(
            title="📵 Call Ended",
            body=f"Call with {caller_number} ended after {mins}m {secs}s.",
            data={"event": "call_ended", "caller": caller_number,
                  "duration": str(duration_seconds)},
        )

    async def notify_scambaiter_started(self, number: str, mode: str):
        await self.send(
            title="🎯 Scambaiter Started",
            body=f"Now calling {number} in {mode.upper()} mode.",
            data={"event": "scambaiter_started", "number": number,
                  "mode": mode},
        )

    async def notify_scambaiter_milestone(self, minutes_wasted: int,
                                          calls_made: int):
        await self.send(
            title="⏱️ Scambaiter Milestone!",
            body=f"{minutes_wasted} minutes wasted across {calls_made} calls!",
            data={"event": "milestone", "minutes": str(minutes_wasted),
                  "calls": str(calls_made)},
        )

    async def notify_recording_ready(self, recording_id: str,
                                     caller_number: str):
        await self.send(
            title="🎙️ Recording Ready",
            body=f"Recording from {caller_number} is ready to play.",
            data={"event": "recording_ready", "recording_id": recording_id,
                  "caller": caller_number},
        )

    async def notify_scam_sync_complete(self, added: int, total: int):
        await self.send(
            title="🔄 Scam DB Updated",
            body=f"Added {added} new scam numbers. Total: {total}.",
            data={"event": "scam_sync", "added": str(added),
                  "total": str(total)},
        )


# Shared singleton
_notifier: Optional[NotificationService] = None


def get_notifier() -> NotificationService:
    global _notifier
    if _notifier is None:
        _notifier = NotificationService()
    return _notifier
