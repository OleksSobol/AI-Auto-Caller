"""
Scambaiter Auto-Caller
Automatically dials known scam numbers, navigates IVR menus,
then wastes scammers' time with an AI persona or looping audio.
"""

import os
import json
import asyncio
import random
import time
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

from ivr_navigator import IVRNavigator
from tts_engine import TTSEngine
from ai_responder import AIResponder

load_dotenv()


class ScamCaller:
    """
    Outbound scambaiter:
      1. Dials a scam number via Twilio (or prints instructions for manual dial)
      2. Auto-navigates IVR menus
      3. Hands off to AI persona or audio loop once a human picks up
    """

    def __init__(self, mode: str = "ai", persona_id: str = "confused_grandma",
                 music_track: str = "never_gonna_give_you_up",
                 tts_engine: str = "gtts", repeat: bool = True,
                 repeat_delay: int = 30):
        """
        Args:
            mode: 'ai' (persona conversation) or 'music' (audio loop)
            persona_id: which persona to use in AI mode
            music_track: which track to loop in music mode
            tts_engine: TTS engine for AI speech
            repeat: auto-redial after call ends
            repeat_delay: seconds to wait between redials
        """
        self.mode = mode
        self.persona_id = persona_id
        self.music_track = music_track
        self.tts_engine = tts_engine
        self.repeat = repeat
        self.repeat_delay = repeat_delay

        # Load personas
        personas_path = Path(__file__).parent / "scambaiter_personas.json"
        with open(personas_path) as f:
            data = json.load(f)
        self.personas = {p["id"]: p for p in data["personas"]}
        self.music_tracks = data["music_tracks"]

        # Load scam numbers
        numbers_path = Path(__file__).parent / "scam_numbers.json"
        with open(numbers_path) as f:
            self.numbers_data = json.load(f)

        self.ivr = IVRNavigator()
        self.tts = TTSEngine(tts_engine)

        # Stats
        self.calls_made = 0
        self.total_time_wasted = 0.0   # seconds
        self.active_call_sid: Optional[str] = None
        self.current_number: Optional[str] = None

        # Twilio client (optional — only if credentials are set)
        self._twilio_client = None
        self._twilio_number = os.getenv("TWILIO_PHONE_NUMBER")
        self._init_twilio()

    # ------------------------------------------------------------------ #
    # Twilio setup                                                         #
    # ------------------------------------------------------------------ #

    def _init_twilio(self):
        sid = os.getenv("TWILIO_ACCOUNT_SID")
        token = os.getenv("TWILIO_AUTH_TOKEN")
        if sid and token:
            try:
                from twilio.rest import Client
                self._twilio_client = Client(sid, token)
                print("✅ Twilio initialised")
            except ImportError:
                print("⚠️  twilio not installed — run: pip install twilio")
        else:
            print("⚠️  Twilio credentials not set — using simulation mode")

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    async def start_campaign(self, number: str):
        """Dial number and repeat until stopped."""
        self.current_number = number
        while True:
            await self._run_single_call(number)
            if not self.repeat:
                break
            print(f"\n⏳ Waiting {self.repeat_delay}s before redialling {number}…")
            await asyncio.sleep(self.repeat_delay)

    async def _run_single_call(self, number: str):
        start = time.time()
        self.calls_made += 1
        print(f"\n📞 Call #{self.calls_made} → {number}")

        if self._twilio_client:
            await self._twilio_call(number)
        else:
            await self._simulate_call(number)

        elapsed = time.time() - start
        self.total_time_wasted += elapsed
        print(f"⏱  Call lasted {elapsed:.0f}s | total wasted: {self.total_time_wasted:.0f}s")

    # ------------------------------------------------------------------ #
    # Twilio outbound call                                                 #
    # ------------------------------------------------------------------ #

    async def _twilio_call(self, number: str):
        """Place real outbound call via Twilio Programmable Voice."""
        twiml = self._build_twiml()
        call = self._twilio_client.calls.create(
            to=number,
            from_=self._twilio_number,
            twiml=twiml,
        )
        self.active_call_sid = call.sid
        print(f"   SID: {call.sid}")

        # Poll until the call is finished
        while True:
            await asyncio.sleep(5)
            status = self._twilio_client.calls(call.sid).fetch().status
            print(f"   Status: {status}")
            if status in ("completed", "failed", "busy", "no-answer", "canceled"):
                break

    def _build_twiml(self) -> str:
        """Build TwiML instructions for Twilio to execute on the call."""
        persona = self.personas.get(self.persona_id, list(self.personas.values())[0])

        if self.mode == "music":
            track = self.music_tracks.get(self.music_track, {})
            local_path = track.get("local_path", "audio/hold_music.mp3")
            # Serve the file via the FastAPI /audio endpoint
            base = os.getenv("PUBLIC_BASE_URL", "http://localhost:8000")
            audio_url = f"{base}/audio/{Path(local_path).name}"
            return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Play loop="0">{audio_url}</Play>
</Response>"""

        # AI persona mode — use a webhook so Twilio calls back our /twilio/voice endpoint
        base = os.getenv("PUBLIC_BASE_URL", "http://localhost:8000")
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say voice="alice">{persona['filler_phrases'][0]}</Say>
  <Gather input="speech" action="{base}/twilio/gather" method="POST"
          speechTimeout="3" timeout="10">
  </Gather>
</Response>"""

    # ------------------------------------------------------------------ #
    # Simulation mode (no Twilio creds)                                   #
    # ------------------------------------------------------------------ #

    async def _simulate_call(self, number: str):
        """
        Simulate the call flow locally — useful for testing without Twilio.
        Prints what would happen step by step.
        """
        persona = self.personas.get(self.persona_id, list(self.personas.values())[0])
        print(f"   [SIM] Mode={self.mode}  Persona={persona['name']}")

        # Simulate IVR navigation
        ivr_prompts = [
            "Thank you for calling. Press 1 for English.",
            "For account questions press 1. To speak with an agent press 0.",
        ]
        for prompt in ivr_prompts:
            await asyncio.sleep(0.5)
            key = self.ivr.decide(prompt)
            print(f"   [IVR] '{prompt}'  →  pressed '{key}'")

        self.ivr.reset()

        # Simulate the engagement phase
        if self.mode == "music":
            print(f"   [MUSIC] Now looping: {self.music_track} (simulated 120s)")
            await asyncio.sleep(2)
        else:
            await self._simulate_ai_conversation(persona)

    async def _simulate_ai_conversation(self, persona: dict):
        """Simulate a back-and-forth AI conversation."""
        responder = AIResponder(use_ai=bool(os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")))
        # Override system prompt with persona
        scammer_lines = [
            "Hello, this is Microsoft support. Your computer has a virus.",
            "I need your credit card number to fix the problem.",
            "Press 1 to confirm you want to protect your computer.",
            "Sir/Ma'am, we need your social security number for verification.",
            "Can you open your computer right now?",
        ]
        print(f"   [AI] Persona: {persona['name']}")
        for scammer_line in scammer_lines:
            await asyncio.sleep(0.3)
            response = self._persona_response(persona, scammer_line, responder)
            print(f"   [SCAMMER] {scammer_line}")
            print(f"   [{persona['name'].upper()}] {response}\n")

    def _persona_response(self, persona: dict, scammer_input: str,
                           responder: AIResponder) -> str:
        """Generate persona response to scammer input."""
        try:
            if responder.use_ai:
                # Inject persona system context into AI call
                return responder._generate_ai_response(
                    f"[PERSONA: {persona['system_prompt']}]\n\nScammer said: {scammer_input}"
                )
        except Exception:
            pass

        # Fallback: random filler phrase
        return random.choice(persona["filler_phrases"])

    # ------------------------------------------------------------------ #
    # Scammer number management                                            #
    # ------------------------------------------------------------------ #

    def add_number(self, number: str, category: str = "other", notes: str = ""):
        """Add a scam number to the list."""
        entry = {"number": number, "category": category, "notes": notes, "calls_made": 0}
        self.numbers_data["numbers"].append(entry)
        self._save_numbers()

    def remove_number(self, number: str):
        """Remove a number from the list."""
        self.numbers_data["numbers"] = [
            n for n in self.numbers_data["numbers"] if n["number"] != number
        ]
        self._save_numbers()

    def get_numbers(self) -> list:
        return self.numbers_data["numbers"]

    def _save_numbers(self):
        path = Path(__file__).parent / "scam_numbers.json"
        with open(path, "w") as f:
            json.dump(self.numbers_data, f, indent=2)

    def get_stats(self) -> dict:
        return {
            "calls_made": self.calls_made,
            "total_time_wasted_seconds": round(self.total_time_wasted),
            "total_time_wasted_minutes": round(self.total_time_wasted / 60, 1),
            "current_number": self.current_number,
            "mode": self.mode,
            "persona": self.persona_id,
            "repeat_enabled": self.repeat,
        }


# ------------------------------------------------------------------ #
# Quick test                                                          #
# ------------------------------------------------------------------ #
if __name__ == "__main__":
    async def demo():
        caller = ScamCaller(mode="ai", persona_id="confused_grandma", repeat=False)
        caller.add_number("+15551234567", "tech_support", "Fake Microsoft support number")
        await caller.start_campaign("+15551234567")
        print("\nStats:", caller.get_stats())

    asyncio.run(demo())
