"""
Call Handler
Manages incoming call events and coordinates AI responses with TTS
"""

import asyncio
from datetime import datetime
from typing import Optional, Dict, List
from tts_engine import TTSEngine
from ai_responder import AIResponder


class CallSession:
    """Represents an active call session"""

    def __init__(self, call_id: str, caller_number: str):
        self.call_id = call_id
        self.caller_number = caller_number
        self.start_time = datetime.now()
        self.end_time = None
        self.messages: List[Dict] = []
        self.status = "active"

    def add_message(self, role: str, content: str, audio_path: Optional[str] = None):
        """Add message to conversation"""
        self.messages.append({
            "timestamp": datetime.now().isoformat(),
            "role": role,
            "content": content,
            "audio_path": audio_path
        })

    def end_call(self):
        """Mark call as ended"""
        self.end_time = datetime.now()
        self.status = "ended"

    def get_duration(self) -> float:
        """Get call duration in seconds"""
        end = self.end_time or datetime.now()
        return (end - self.start_time).total_seconds()

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "call_id": self.call_id,
            "caller_number": self.caller_number,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration": self.get_duration(),
            "status": self.status,
            "messages": self.messages
        }


class CallHandler:
    """Main call handling coordinator"""

    def __init__(self, tts_engine: str = "gtts", use_ai: bool = False):
        """
        Initialize call handler

        Args:
            tts_engine: TTS engine to use (elevenlabs, gtts, pyttsx3)
            use_ai: Whether to use AI for dynamic responses
        """
        self.tts = TTSEngine(tts_engine)
        self.ai_responder = AIResponder(use_ai=use_ai)
        self.active_calls: Dict[str, CallSession] = {}
        self.call_history: List[CallSession] = []
        self.auto_answer_enabled = True
        self.max_call_duration = 300  # 5 minutes max

    async def handle_incoming_call(self, call_id: str, caller_number: str) -> Dict:
        """
        Handle incoming call

        Args:
            call_id: Unique call identifier
            caller_number: Caller's phone number

        Returns:
            Call session information
        """
        if not self.auto_answer_enabled:
            return {"status": "rejected", "reason": "Auto-answer disabled"}

        # Create call session
        session = CallSession(call_id, caller_number)
        self.active_calls[call_id] = session

        # Answer call with greeting
        await self._send_response(session, context="greeting")

        return {
            "status": "answered",
            "call_id": call_id,
            "message": "Call answered successfully"
        }

    async def process_user_speech(self, call_id: str, user_text: str) -> Dict:
        """
        Process user's speech and generate response

        Args:
            call_id: Call identifier
            user_text: Transcribed user speech

        Returns:
            Response information
        """
        if call_id not in self.active_calls:
            return {"error": "Call session not found"}

        session = self.active_calls[call_id]

        # Add user message to session
        session.add_message("user", user_text)

        # Check for end call keywords
        if self._should_end_call(user_text):
            return await self.end_call(call_id)

        # Generate and send AI response
        response_text = self.ai_responder.generate_response(user_text)
        await self._send_response(session, response_text=response_text)

        return {
            "status": "success",
            "response": response_text,
            "call_duration": session.get_duration()
        }

    async def _send_response(
        self,
        session: CallSession,
        response_text: Optional[str] = None,
        context: Optional[str] = None
    ):
        """
        Generate and send TTS response

        Args:
            session: Call session
            response_text: Response text (if not using context)
            context: Response context (greeting, goodbye, etc.)
        """
        # Get response text
        if response_text is None:
            if context:
                response_text = self.ai_responder.generate_response(context=context)
            else:
                response_text = self.ai_responder.get_greeting()

        # Generate TTS audio
        try:
            audio_path = f"/tmp/call_{session.call_id}_{len(session.messages)}.mp3"
            audio_bytes = await self.tts.text_to_speech(response_text, audio_path)

            # Add to session
            session.add_message("assistant", response_text, audio_path)

            # TODO: Play audio to caller (integration with telephony system)
            print(f"[TTS] Generated audio for: {response_text[:50]}...")

        except Exception as e:
            print(f"TTS Error: {e}")
            session.add_message("assistant", response_text)

    def _should_end_call(self, user_text: str) -> bool:
        """Check if user wants to end call"""
        end_keywords = [
            "goodbye", "bye", "hang up", "end call",
            "that's all", "thank you bye", "talk later"
        ]
        return any(keyword in user_text.lower() for keyword in end_keywords)

    async def end_call(self, call_id: str) -> Dict:
        """
        End active call

        Args:
            call_id: Call identifier

        Returns:
            Call summary
        """
        if call_id not in self.active_calls:
            return {"error": "Call session not found"}

        session = self.active_calls[call_id]

        # Send goodbye message
        await self._send_response(session, context="goodbye")

        # End session
        session.end_call()

        # Move to history
        self.call_history.append(session)
        del self.active_calls[call_id]

        # Reset AI conversation
        self.ai_responder.reset_conversation()

        return {
            "status": "ended",
            "duration": session.get_duration(),
            "message_count": len(session.messages),
            "summary": session.to_dict()
        }

    def get_active_calls(self) -> List[Dict]:
        """Get all active call sessions"""
        return [session.to_dict() for session in self.active_calls.values()]

    def get_call_history(self, limit: int = 10) -> List[Dict]:
        """Get call history"""
        return [
            session.to_dict()
            for session in self.call_history[-limit:]
        ]

    def toggle_auto_answer(self, enabled: bool):
        """Enable or disable auto-answer"""
        self.auto_answer_enabled = enabled

    def update_settings(self, settings: Dict):
        """Update handler settings"""
        if "tts_engine" in settings:
            self.tts = TTSEngine(settings["tts_engine"])
        if "use_ai" in settings:
            self.ai_responder.use_ai = settings["use_ai"]
        if "auto_answer" in settings:
            self.auto_answer_enabled = settings["auto_answer"]
        if "max_call_duration" in settings:
            self.max_call_duration = settings["max_call_duration"]


# Example usage
if __name__ == "__main__":
    async def test():
        handler = CallHandler(tts_engine="gtts")

        # Simulate incoming call
        result = await handler.handle_incoming_call("call_001", "+1234567890")
        print("Call answered:", result)

        # Simulate user speech
        await asyncio.sleep(1)
        result = await handler.process_user_speech(
            "call_001",
            "I'd like to schedule an appointment"
        )
        print("Response:", result)

        # End call
        await asyncio.sleep(1)
        result = await handler.end_call("call_001")
        print("Call ended:", result)

    asyncio.run(test())
