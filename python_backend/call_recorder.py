"""
Call Recorder
Records calls (inbound and outbound), stores them, and provides playback.
"""

import os
import json
import uuid
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict
from dotenv import load_dotenv

load_dotenv()

RECORDINGS_DIR = Path(__file__).parent / "recordings"
RECORDINGS_DIR.mkdir(exist_ok=True)

METADATA_FILE = RECORDINGS_DIR / "index.json"


def _load_index() -> List[Dict]:
    if METADATA_FILE.exists():
        with open(METADATA_FILE) as f:
            return json.load(f)
    return []


def _save_index(index: List[Dict]):
    with open(METADATA_FILE, "w") as f:
        json.dump(index, f, indent=2)


class CallRecorder:
    """Manages call recording for both inbound and outbound calls"""

    def __init__(self):
        self.active_recordings: Dict[str, dict] = {}   # call_id → metadata
        self._twilio_client = None
        self._init_twilio()

    def _init_twilio(self):
        sid = os.getenv("TWILIO_ACCOUNT_SID")
        token = os.getenv("TWILIO_AUTH_TOKEN")
        if sid and token:
            try:
                from twilio.rest import Client
                self._twilio_client = Client(sid, token)
            except ImportError:
                pass

    # ------------------------------------------------------------------ #
    # Start / stop recording                                               #
    # ------------------------------------------------------------------ #

    def start_recording(self, call_id: str, caller_number: str,
                        direction: str = "inbound") -> Dict:
        """
        Begin recording a call.

        For Twilio calls this triggers a server-side recording.
        For simulated calls it sets up local audio capture.
        """
        meta = {
            "recording_id": str(uuid.uuid4())[:8],
            "call_id": call_id,
            "caller_number": caller_number,
            "direction": direction,
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "duration_seconds": None,
            "file_path": None,
            "twilio_recording_sid": None,
            "status": "recording",
        }
        self.active_recordings[call_id] = meta
        return meta

    def stop_recording(self, call_id: str,
                       audio_bytes: Optional[bytes] = None) -> Optional[Dict]:
        """Stop recording and persist metadata + optional local audio."""
        meta = self.active_recordings.pop(call_id, None)
        if not meta:
            return None

        meta["end_time"] = datetime.now().isoformat()
        start = datetime.fromisoformat(meta["start_time"])
        end = datetime.fromisoformat(meta["end_time"])
        meta["duration_seconds"] = round((end - start).total_seconds())
        meta["status"] = "completed"

        # Save local audio if provided
        if audio_bytes:
            file_name = f"{meta['recording_id']}_{call_id}.wav"
            file_path = RECORDINGS_DIR / file_name
            with open(file_path, "wb") as f:
                f.write(audio_bytes)
            meta["file_path"] = str(file_path)

        # Persist to index
        index = _load_index()
        index.insert(0, meta)
        _save_index(index)

        return meta

    # ------------------------------------------------------------------ #
    # Twilio server-side recording                                         #
    # ------------------------------------------------------------------ #

    def enable_twilio_recording(self, call_sid: str) -> Optional[str]:
        """Tell Twilio to record an active call. Returns recording SID."""
        if not self._twilio_client:
            return None
        try:
            rec = self._twilio_client.calls(call_sid).recordings.create()
            return rec.sid
        except Exception as e:
            print(f"Twilio recording error: {e}")
            return None

    async def fetch_twilio_recording(self, recording_sid: str,
                                     call_id: str) -> Optional[str]:
        """
        Download a completed Twilio recording and store it locally.
        Returns local file path.
        """
        if not self._twilio_client:
            return None
        try:
            import aiohttp
            rec = self._twilio_client.recordings(recording_sid).fetch()
            url = f"https://api.twilio.com{rec.uri.replace('.json', '.mp3')}"
            sid_b64 = f"{os.getenv('TWILIO_ACCOUNT_SID')}:{os.getenv('TWILIO_AUTH_TOKEN')}"
            import base64
            auth = base64.b64encode(sid_b64.encode()).decode()

            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers={"Authorization": f"Basic {auth}"}) as r:
                    if r.status == 200:
                        audio = await r.read()
                        file_path = RECORDINGS_DIR / f"{recording_sid}.mp3"
                        with open(file_path, "wb") as f:
                            f.write(audio)

                        # Update index entry
                        index = _load_index()
                        for entry in index:
                            if entry.get("call_id") == call_id:
                                entry["file_path"] = str(file_path)
                                entry["twilio_recording_sid"] = recording_sid
                        _save_index(index)
                        return str(file_path)
        except Exception as e:
            print(f"Error downloading Twilio recording: {e}")
        return None

    # ------------------------------------------------------------------ #
    # Query                                                                #
    # ------------------------------------------------------------------ #

    def get_recordings(self, limit: int = 20) -> List[Dict]:
        return _load_index()[:limit]

    def get_recording(self, recording_id: str) -> Optional[Dict]:
        index = _load_index()
        return next((r for r in index if r["recording_id"] == recording_id), None)

    def delete_recording(self, recording_id: str) -> bool:
        index = _load_index()
        entry = next((r for r in index if r["recording_id"] == recording_id), None)
        if not entry:
            return False

        # Delete file
        if entry.get("file_path"):
            path = Path(entry["file_path"])
            if path.exists():
                path.unlink()

        # Remove from index
        _save_index([r for r in index if r["recording_id"] != recording_id])
        return True

    def get_stats(self) -> Dict:
        index = _load_index()
        total_seconds = sum(r.get("duration_seconds") or 0 for r in index)
        return {
            "total_recordings": len(index),
            "total_duration_minutes": round(total_seconds / 60, 1),
            "active_recordings": len(self.active_recordings),
        }
