"""
Text-to-Speech Engine
Supports multiple TTS providers: ElevenLabs, gTTS, and pyttsx3
"""

import os
import io
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class TTSEngine:
    """Unified TTS engine supporting multiple providers"""

    def __init__(self, engine: str = "gtts"):
        """
        Initialize TTS engine

        Args:
            engine: TTS provider - 'elevenlabs', 'gtts', or 'pyttsx3'
        """
        self.engine = engine.lower()
        self.elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
        self.voice_id = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")

    async def text_to_speech(self, text: str, output_path: Optional[str] = None) -> bytes:
        """
        Convert text to speech audio

        Args:
            text: Text to convert to speech
            output_path: Optional path to save audio file

        Returns:
            Audio bytes
        """
        if self.engine == "elevenlabs":
            return await self._elevenlabs_tts(text, output_path)
        elif self.engine == "gtts":
            return await self._gtts_tts(text, output_path)
        elif self.engine == "pyttsx3":
            return await self._pyttsx3_tts(text, output_path)
        else:
            raise ValueError(f"Unknown TTS engine: {self.engine}")

    async def _elevenlabs_tts(self, text: str, output_path: Optional[str] = None) -> bytes:
        """ElevenLabs TTS (Premium)"""
        try:
            from elevenlabs import generate, save, Voice

            if not self.elevenlabs_api_key:
                raise ValueError("ElevenLabs API key not configured")

            # Set API key
            os.environ["ELEVEN_API_KEY"] = self.elevenlabs_api_key

            # Generate audio
            audio = generate(
                text=text,
                voice=Voice(voice_id=self.voice_id),
                model="eleven_monolingual_v1"
            )

            # Convert to bytes
            if isinstance(audio, bytes):
                audio_bytes = audio
            else:
                audio_bytes = b"".join(audio)

            # Save if path provided
            if output_path:
                with open(output_path, "wb") as f:
                    f.write(audio_bytes)

            return audio_bytes

        except ImportError:
            raise ImportError("ElevenLabs not installed. Run: pip install elevenlabs")
        except Exception as e:
            raise Exception(f"ElevenLabs TTS failed: {str(e)}")

    async def _gtts_tts(self, text: str, output_path: Optional[str] = None) -> bytes:
        """Google TTS (Free, requires internet)"""
        try:
            from gtts import gTTS

            # Create TTS object
            tts = gTTS(text=text, lang='en', slow=False)

            # Save to bytes
            audio_fp = io.BytesIO()
            tts.write_to_fp(audio_fp)
            audio_bytes = audio_fp.getvalue()

            # Save if path provided
            if output_path:
                with open(output_path, "wb") as f:
                    f.write(audio_bytes)

            return audio_bytes

        except ImportError:
            raise ImportError("gTTS not installed. Run: pip install gTTS")
        except Exception as e:
            raise Exception(f"gTTS failed: {str(e)}")

    async def _pyttsx3_tts(self, text: str, output_path: Optional[str] = None) -> bytes:
        """pyttsx3 TTS (Free, offline)"""
        try:
            import pyttsx3

            if not output_path:
                output_path = "/tmp/tts_output.mp3"

            # Initialize engine
            engine = pyttsx3.init()

            # Configure voice properties
            engine.setProperty('rate', 150)  # Speed
            engine.setProperty('volume', 0.9)  # Volume

            # Save to file
            engine.save_to_file(text, output_path)
            engine.runAndWait()

            # Read file to bytes
            with open(output_path, "rb") as f:
                audio_bytes = f.read()

            return audio_bytes

        except ImportError:
            raise ImportError("pyttsx3 not installed. Run: pip install pyttsx3")
        except Exception as e:
            raise Exception(f"pyttsx3 TTS failed: {str(e)}")

    def get_available_voices(self) -> list:
        """Get list of available voices for current engine"""
        if self.engine == "elevenlabs":
            return self._get_elevenlabs_voices()
        elif self.engine == "pyttsx3":
            return self._get_pyttsx3_voices()
        else:
            return ["default"]

    def _get_elevenlabs_voices(self) -> list:
        """Get ElevenLabs voices"""
        try:
            from elevenlabs import voices
            return [{"id": v.voice_id, "name": v.name} for v in voices()]
        except:
            return [{"id": self.voice_id, "name": "Default"}]

    def _get_pyttsx3_voices(self) -> list:
        """Get pyttsx3 voices"""
        try:
            import pyttsx3
            engine = pyttsx3.init()
            voices = engine.getProperty('voices')
            return [{"id": v.id, "name": v.name} for v in voices]
        except:
            return [{"id": "default", "name": "Default"}]


# Example usage
if __name__ == "__main__":
    import asyncio

    async def test():
        # Test with gTTS (free)
        tts = TTSEngine("gtts")
        audio = await tts.text_to_speech("Hello! This is a test of the automated phone system.")
        print(f"Generated {len(audio)} bytes of audio")

    asyncio.run(test())
