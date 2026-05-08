"""
Speech-to-Text Engine
Supports Whisper (local, free) and Google Speech Recognition (free tier)
Used for transcribing what callers say during live calls.
"""

import io
import os
import wave
import tempfile
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class STTEngine:
    """Unified speech-to-text supporting Whisper and Google STT"""

    def __init__(self, engine: str = "whisper"):
        """
        Args:
            engine: 'whisper' (local, free) or 'google' (free tier, needs internet)
        """
        self.engine = engine.lower()
        self._whisper_model = None   # lazy-loaded

    def transcribe(self, audio_bytes: bytes, sample_rate: int = 16000) -> str:
        """
        Transcribe audio bytes to text.

        Args:
            audio_bytes: Raw PCM audio or WAV bytes
            sample_rate: Audio sample rate in Hz

        Returns:
            Transcribed text string
        """
        if self.engine == "whisper":
            return self._whisper_transcribe(audio_bytes, sample_rate)
        elif self.engine == "google":
            return self._google_transcribe(audio_bytes, sample_rate)
        else:
            raise ValueError(f"Unknown STT engine: {self.engine}")

    def transcribe_file(self, file_path: str) -> str:
        """Transcribe an audio file (WAV/MP3/M4A)"""
        with open(file_path, "rb") as f:
            audio_bytes = f.read()
        return self.transcribe(audio_bytes)

    # ------------------------------------------------------------------ #
    # Whisper (local, fully free, runs on CPU)                            #
    # ------------------------------------------------------------------ #

    def _load_whisper(self):
        if self._whisper_model is None:
            try:
                import whisper
                model_size = os.getenv("WHISPER_MODEL", "base")  # tiny/base/small/medium
                print(f"Loading Whisper model '{model_size}'...")
                self._whisper_model = whisper.load_model(model_size)
            except ImportError:
                raise ImportError("openai-whisper not installed. Run: pip install openai-whisper")
        return self._whisper_model

    def _whisper_transcribe(self, audio_bytes: bytes, sample_rate: int) -> str:
        model = self._load_whisper()

        # Write to temp WAV file (Whisper reads files)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = tmp.name
            with wave.open(tmp_path, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)   # 16-bit
                wf.setframerate(sample_rate)
                wf.writeframes(audio_bytes)

        try:
            result = model.transcribe(tmp_path, language="en", fp16=False)
            return result["text"].strip()
        finally:
            os.unlink(tmp_path)

    # ------------------------------------------------------------------ #
    # Google Speech Recognition (free tier via SpeechRecognition library) #
    # ------------------------------------------------------------------ #

    def _google_transcribe(self, audio_bytes: bytes, sample_rate: int) -> str:
        try:
            import speech_recognition as sr
        except ImportError:
            raise ImportError("SpeechRecognition not installed. Run: pip install SpeechRecognition")

        recognizer = sr.Recognizer()

        # Convert raw PCM to AudioData
        with io.BytesIO() as buf:
            with wave.open(buf, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sample_rate)
                wf.writeframes(audio_bytes)
            buf.seek(0)
            with sr.AudioFile(buf) as source:
                audio = recognizer.record(source)

        try:
            return recognizer.recognize_google(audio)
        except sr.UnknownValueError:
            return ""
        except sr.RequestError as e:
            raise Exception(f"Google STT API error: {e}")

    # ------------------------------------------------------------------ #
    # Streaming transcription via Twilio Media Streams (WebSocket)        #
    # ------------------------------------------------------------------ #

    async def transcribe_twilio_stream(self, websocket, on_transcript):
        """
        Receive mulaw audio from Twilio Media Streams WebSocket,
        buffer it, and call on_transcript(text) with each chunk.

        Usage: mount the /ws/media-stream endpoint and pass the WS here.
        """
        import asyncio
        import base64
        import audioop
        import json

        audio_buffer = b""
        CHUNK_SECONDS = 2
        CHUNK_BYTES = 8000 * CHUNK_SECONDS  # 8kHz mulaw = 8000 bytes/sec

        async for message in websocket.iter_text():
            data = json.loads(message)
            event = data.get("event")

            if event == "media":
                # Twilio sends base64-encoded mulaw 8kHz audio
                payload = base64.b64decode(data["media"]["payload"])
                # Convert mulaw → 16-bit PCM
                pcm = audioop.ulaw2lin(payload, 2)
                # Upsample 8kHz → 16kHz for better Whisper accuracy
                pcm16k, _ = audioop.ratecv(pcm, 2, 1, 8000, 16000, None)
                audio_buffer += pcm16k

                if len(audio_buffer) >= CHUNK_BYTES * 2:  # *2 because 16kHz
                    text = self.transcribe(audio_buffer, sample_rate=16000)
                    audio_buffer = b""
                    if text:
                        await on_transcript(text)

            elif event == "stop":
                # Final chunk
                if audio_buffer:
                    text = self.transcribe(audio_buffer, sample_rate=16000)
                    if text:
                        await on_transcript(text)
                break


if __name__ == "__main__":
    stt = STTEngine("google")
    # Quick test: synthesize speech then transcribe it
    print("STT engine initialized. Use transcribe(audio_bytes) to transcribe audio.")
    print(f"Engine: {stt.engine}")
