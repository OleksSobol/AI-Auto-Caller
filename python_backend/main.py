"""
FastAPI Server for AI Auto Caller
Provides REST API for call handling, TTS, AI responses, recordings,
push notifications, scam number sync, and a live web dashboard.
"""

import os
import uuid
import asyncio
import random
import json
from pathlib import Path
from typing import Optional, List, Set
from fastapi import FastAPI, HTTPException, Form, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from call_handler import CallHandler
from ai_responder import AIResponder
from tts_engine import TTSEngine
from stt_engine import STTEngine
from call_recorder import CallRecorder
from scam_caller import ScamCaller
from ivr_navigator import IVRNavigator
from notification_service import get_notifier
from scam_db_sync import sync_scam_numbers, start_auto_sync

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="AI Auto Caller API",
    description="Automatic phone call answering with AI-powered responses",
    version="2.0.0"
)

# Serve web dashboard at /dashboard
DASHBOARD_DIR = Path(__file__).parent / "dashboard"
app.mount("/dashboard", StaticFiles(directory=str(DASHBOARD_DIR), html=True), name="dashboard")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Core services ──────────────────────────────────────────────────────────── #
call_handler = CallHandler(
    tts_engine=os.getenv("DEFAULT_TTS_ENGINE", "gtts"),
    use_ai=bool(os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY"))
)
stt_engine = STTEngine(engine=os.getenv("DEFAULT_STT_ENGINE", "google"))
recorder   = CallRecorder()
notifier   = get_notifier()

# ── Scambaiter globals ─────────────────────────────────────────────────────── #
_scam_caller: Optional[ScamCaller] = None
_scam_task: Optional[asyncio.Task] = None


# ── WebSocket broadcast ────────────────────────────────────────────────────── #
_ws_clients: Set[WebSocket] = set()


async def broadcast(event: str, data: dict):
    """Push a JSON event to all connected dashboard clients."""
    message = json.dumps({"event": event, "data": data})
    dead = set()
    for ws in _ws_clients:
        try:
            await ws.send_text(message)
        except Exception:
            dead.add(ws)
    _ws_clients -= dead


@app.websocket("/ws/dashboard")
async def ws_dashboard(websocket: WebSocket):
    await websocket.accept()
    _ws_clients.add(websocket)
    try:
        while True:
            await websocket.receive_text()   # keep-alive; client sends nothing
    except WebSocketDisconnect:
        _ws_clients.discard(websocket)


# ── Startup tasks ──────────────────────────────────────────────────────────── #
@app.on_event("startup")
async def on_startup():
    if os.getenv("AUTO_SYNC_SCAM_DB", "false").lower() == "true":
        asyncio.create_task(start_auto_sync(
            interval_hours=int(os.getenv("SYNC_INTERVAL_HOURS", "24"))
        ))


# ── Pydantic models ────────────────────────────────────────────────────────── #
class IncomingCall(BaseModel):
    call_id: Optional[str] = None
    caller_number: str


class TranscribeRequest(BaseModel):
    call_id: str
    audio_base64: str                  # base64-encoded raw PCM bytes
    sample_rate: int = 16000
    engine: Optional[str] = None      # overrides server default


class UserSpeech(BaseModel):
    call_id: str
    text: str


class TTSRequest(BaseModel):
    text: str
    engine: Optional[str] = "gtts"


class ResponseUpdate(BaseModel):
    category: str
    text: str


class SettingsUpdate(BaseModel):
    tts_engine: Optional[str] = None
    use_ai: Optional[bool] = None
    auto_answer: Optional[bool] = None
    max_call_duration: Optional[int] = None


class ScamNumberAdd(BaseModel):
    number: str
    category: str = "other"
    notes: str = ""


class ScamCampaignStart(BaseModel):
    number: str
    mode: str = "ai"              # 'ai' or 'music'
    persona_id: str = "confused_grandma"
    music_track: str = "never_gonna_give_you_up"
    tts_engine: str = "gtts"
    repeat: bool = True
    repeat_delay: int = 30        # seconds between redials


# API Routes

@app.get("/")
async def root():
    """API status endpoint"""
    return {
        "app": "AI Auto Caller",
        "version": "1.0.0",
        "status": "running",
        "auto_answer_enabled": call_handler.auto_answer_enabled
    }


@app.post("/api/answer-call")
async def answer_call(call: IncomingCall):
    """Auto-answer incoming call, start recording, push notification."""
    try:
        if not call.call_id:
            call.call_id = f"call_{uuid.uuid4().hex[:8]}"

        result = await call_handler.handle_incoming_call(
            call.call_id, call.caller_number
        )

        if result.get("status") == "answered":
            # Start recording
            recorder.start_recording(call.call_id, call.caller_number, "inbound")
            # Push notification
            asyncio.create_task(notifier.notify_call_answered(
                call.caller_number, call.call_id
            ))
            # Broadcast to dashboard
            asyncio.create_task(broadcast("call_answered", {
                "caller": call.caller_number, "call_id": call.call_id
            }))

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/transcribe")
async def transcribe_audio(req: TranscribeRequest):
    """
    Transcribe base64-encoded audio to text using Whisper or Google STT.
    Optionally process the transcript as user speech for an active call.
    """
    import base64
    try:
        audio_bytes = base64.b64decode(req.audio_base64)
        engine = req.engine or stt_engine.engine
        local_stt = STTEngine(engine)
        text = local_stt.transcribe(audio_bytes, req.sample_rate)

        # If there's an active call with this ID, feed the transcript in
        if req.call_id in call_handler.active_calls and text:
            asyncio.create_task(broadcast("transcript", {
                "call_id": req.call_id, "role": "user", "text": text
            }))

        return {"call_id": req.call_id, "transcript": text, "engine": engine}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/process-speech")
async def process_speech(speech: UserSpeech):
    """Process user speech, generate AI response, broadcast transcript."""
    try:
        result = await call_handler.process_user_speech(
            speech.call_id, speech.text
        )
        # Broadcast both sides to dashboard
        asyncio.create_task(broadcast("transcript", {
            "call_id": speech.call_id, "role": "user", "text": speech.text
        }))
        if "response" in result:
            asyncio.create_task(broadcast("transcript", {
                "call_id": speech.call_id, "role": "assistant",
                "text": result["response"]
            }))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/end-call/{call_id}")
async def end_call(call_id: str):
    """End active call, stop recording, push notification."""
    try:
        result = await call_handler.end_call(call_id)
        # Stop recording
        rec_meta = recorder.stop_recording(call_id)
        if rec_meta:
            asyncio.create_task(notifier.notify_recording_ready(
                rec_meta["recording_id"],
                rec_meta["caller_number"]
            ))
            asyncio.create_task(broadcast("recording", {
                "recording_id": rec_meta["recording_id"],
                "caller": rec_meta["caller_number"]
            }))
        duration = result.get("duration", 0)
        asyncio.create_task(notifier.notify_call_ended(
            result.get("summary", {}).get("caller_number", "Unknown"), duration
        ))
        asyncio.create_task(broadcast("call_ended", {
            "call_id": call_id, "duration": duration
        }))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/active-calls")
async def get_active_calls():
    """Get all active call sessions"""
    return {
        "active_calls": call_handler.get_active_calls(),
        "count": len(call_handler.active_calls)
    }


@app.get("/api/call-history")
async def get_call_history(limit: int = 10):
    """Get call history"""
    return {
        "history": call_handler.get_call_history(limit),
        "total": len(call_handler.call_history)
    }


@app.get("/api/responses")
async def get_responses():
    """Get all predefined responses"""
    return call_handler.ai_responder.get_all_responses()


@app.post("/api/responses")
async def add_response(response_text: str):
    """Add new custom response"""
    try:
        call_handler.ai_responder.add_custom_response(response_text)
        return {"status": "success", "message": "Response added"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/responses")
async def update_response(update: ResponseUpdate):
    """Update a specific response category"""
    try:
        call_handler.ai_responder.update_response(
            update.category,
            update.text
        )
        return {"status": "success", "message": "Response updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/tts")
async def text_to_speech(request: TTSRequest):
    """
    Convert text to speech

    Returns audio file
    """
    try:
        tts = TTSEngine(request.engine)
        output_path = f"/tmp/tts_{uuid.uuid4().hex[:8]}.mp3"

        await tts.text_to_speech(request.text, output_path)

        return FileResponse(
            output_path,
            media_type="audio/mpeg",
            filename="speech.mp3"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/voices")
async def get_voices(engine: str = "gtts"):
    """Get available TTS voices"""
    try:
        tts = TTSEngine(engine)
        voices = tts.get_available_voices()
        return {"engine": engine, "voices": voices}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/settings")
async def update_settings(settings: SettingsUpdate):
    """Update system settings"""
    try:
        settings_dict = settings.dict(exclude_none=True)
        call_handler.update_settings(settings_dict)
        return {
            "status": "success",
            "message": "Settings updated",
            "settings": settings_dict
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/settings/auto-answer")
async def toggle_auto_answer(enabled: bool):
    """Toggle auto-answer on/off"""
    call_handler.toggle_auto_answer(enabled)
    return {
        "status": "success",
        "auto_answer_enabled": enabled
    }


@app.get("/api/settings")
async def get_settings():
    """Get current settings"""
    return {
        "tts_engine": call_handler.tts.engine,
        "auto_answer_enabled": call_handler.auto_answer_enabled,
        "max_call_duration": call_handler.max_call_duration,
        "use_ai": call_handler.ai_responder.use_ai
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "active_calls": len(call_handler.active_calls),
        "total_calls_processed": len(call_handler.call_history),
        "recordings": recorder.get_stats(),
        "dashboard_clients": len(_ws_clients),
    }


# ============================================================ #
#  RECORDINGS ENDPOINTS                                         #
# ============================================================ #

@app.get("/api/recordings")
async def list_recordings(limit: int = 20):
    return {"recordings": recorder.get_recordings(limit),
            **recorder.get_stats()}


@app.get("/api/recordings/{recording_id}")
async def get_recording(recording_id: str):
    rec = recorder.get_recording(recording_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Recording not found")
    return rec


@app.get("/api/recordings/{recording_id}/audio")
async def stream_recording(recording_id: str):
    rec = recorder.get_recording(recording_id)
    if not rec or not rec.get("file_path"):
        raise HTTPException(status_code=404, detail="Audio file not found")
    path = Path(rec["file_path"])
    if not path.exists():
        raise HTTPException(status_code=404, detail="Audio file missing on disk")
    media = "audio/mpeg" if path.suffix == ".mp3" else "audio/wav"
    return FileResponse(str(path), media_type=media)


@app.delete("/api/recordings/{recording_id}")
async def delete_recording(recording_id: str):
    if recorder.delete_recording(recording_id):
        return {"status": "deleted"}
    raise HTTPException(status_code=404, detail="Recording not found")


# ============================================================ #
#  NOTIFICATIONS ENDPOINTS                                      #
# ============================================================ #

@app.post("/api/notifications/register")
async def register_device(token: str):
    """Register an FCM device token for push notifications."""
    notifier.register_token(token)
    return {"status": "registered"}


@app.delete("/api/notifications/register")
async def unregister_device(token: str):
    notifier.unregister_token(token)
    return {"status": "unregistered"}


@app.post("/api/notifications/test")
async def send_test_notification():
    ok = await notifier.send("🧪 Test Notification",
                             "AI Auto Caller is working!")
    return {"sent": ok}


# ============================================================ #
#  SCAM NUMBER SYNC ENDPOINTS                                   #
# ============================================================ #

@app.post("/api/scambaiter/sync")
async def trigger_scam_sync():
    """Manually trigger a scam number database sync from public sources."""
    result = await sync_scam_numbers(notify=True)
    asyncio.create_task(broadcast("sync_done", result))
    return result


@app.get("/api/scambaiter/sync/status")
async def sync_status():
    import json
    from scam_db_sync import NUMBERS_FILE
    if NUMBERS_FILE.exists():
        with open(NUMBERS_FILE) as f:
            data = json.load(f)
        return {
            "total_numbers": len(data.get("numbers", [])),
            "last_sync": data.get("last_sync"),
        }
    return {"total_numbers": 0, "last_sync": None}


# ============================================================ #
#  SCAMBAITER ENDPOINTS                                         #
# ============================================================ #

@app.get("/api/scambaiter/personas")
async def get_personas():
    """List all available AI personas for scambaiting"""
    import json
    path = Path(__file__).parent / "scambaiter_personas.json"
    with open(path) as f:
        data = json.load(f)
    return {
        "personas": data["personas"],
        "music_tracks": list(data["music_tracks"].keys()),
    }


@app.get("/api/scambaiter/numbers")
async def get_scam_numbers():
    """Get the list of tracked scam numbers"""
    caller = ScamCaller.__new__(ScamCaller)
    caller.__init__.__func__  # avoid real __init__
    import json
    path = Path(__file__).parent / "scam_numbers.json"
    with open(path) as f:
        data = json.load(f)
    return data


@app.post("/api/scambaiter/numbers")
async def add_scam_number(entry: ScamNumberAdd):
    """Add a scam number to the list"""
    sc = ScamCaller(repeat=False)
    sc.add_number(entry.number, entry.category, entry.notes)
    return {"status": "added", "number": entry.number}


@app.delete("/api/scambaiter/numbers/{number}")
async def delete_scam_number(number: str):
    """Remove a scam number from the list"""
    sc = ScamCaller(repeat=False)
    sc.remove_number(number)
    return {"status": "removed", "number": number}


@app.post("/api/scambaiter/start")
async def start_scam_campaign(campaign: ScamCampaignStart):
    """
    Start an automated scambaiter campaign.

    Dials the scam number, navigates IVR menus, then either:
    - mode='ai'    → engages scammer with a chosen AI persona
    - mode='music' → loops an audio file (e.g. Never Gonna Give You Up)

    With repeat=true the dialer redials automatically after each call ends.
    """
    global _scam_caller, _scam_task

    if _scam_task and not _scam_task.done():
        raise HTTPException(status_code=409, detail="A campaign is already running. Stop it first.")

    _scam_caller = ScamCaller(
        mode=campaign.mode,
        persona_id=campaign.persona_id,
        music_track=campaign.music_track,
        tts_engine=campaign.tts_engine,
        repeat=campaign.repeat,
        repeat_delay=campaign.repeat_delay,
    )

    # Run in background so the HTTP response returns immediately
    _scam_task = asyncio.create_task(
        _scam_caller.start_campaign(campaign.number)
    )

    asyncio.create_task(notifier.notify_scambaiter_started(
        campaign.number, campaign.mode
    ))
    asyncio.create_task(broadcast("scam_update", {
        "running": True, "current_number": campaign.number,
        "mode": campaign.mode, "persona": campaign.persona_id,
        "calls_made": 0, "total_time_wasted_minutes": 0,
    }))

    return {
        "status": "started",
        "number": campaign.number,
        "mode": campaign.mode,
        "persona": campaign.persona_id if campaign.mode == "ai" else None,
        "music_track": campaign.music_track if campaign.mode == "music" else None,
        "repeat": campaign.repeat,
        "repeat_delay_seconds": campaign.repeat_delay,
        "message": "Campaign running in background. Use /api/scambaiter/status to monitor."
    }


@app.post("/api/scambaiter/stop")
async def stop_scam_campaign():
    """Stop the currently running scambaiter campaign"""
    global _scam_task, _scam_caller

    if not _scam_task or _scam_task.done():
        return {"status": "not_running"}

    _scam_task.cancel()
    stats = _scam_caller.get_stats() if _scam_caller else {}
    _scam_caller = None
    _scam_task = None

    asyncio.create_task(broadcast("scam_update", {"running": False, **stats}))
    return {"status": "stopped", "stats": stats}


@app.get("/api/scambaiter/status")
async def scam_campaign_status():
    """Get current campaign status and stats"""
    if not _scam_task or _scam_task.done():
        return {"running": False}

    stats = _scam_caller.get_stats() if _scam_caller else {}
    return {"running": True, **stats}


@app.post("/api/scambaiter/test-ivr")
async def test_ivr(prompt: str):
    """Test the IVR navigator against a prompt string"""
    nav = IVRNavigator()
    key = nav.decide(prompt)
    return {"prompt": prompt, "key_to_press": key}


# ============================================================ #
#  TWILIO WEBHOOKS  (called by Twilio during live calls)        #
# ============================================================ #

@app.post("/twilio/voice")
async def twilio_voice_webhook(request: Request):
    """
    Twilio calls this webhook when the outbound call is answered.
    Returns TwiML telling Twilio what to say/play and how to gather speech.
    """
    import json
    personas_path = Path(__file__).parent / "scambaiter_personas.json"
    with open(personas_path) as f:
        data = json.load(f)

    persona_id = _scam_caller.persona_id if _scam_caller else "confused_grandma"
    personas = {p["id"]: p for p in data["personas"]}
    persona = personas.get(persona_id, data["personas"][0])
    filler = random.choice(persona["filler_phrases"])

    base = os.getenv("PUBLIC_BASE_URL", "http://localhost:8000")
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say voice="alice">{filler}</Say>
  <Gather input="speech" action="{base}/twilio/gather" method="POST"
          speechTimeout="3" timeout="15">
    <Say voice="alice">Go ahead.</Say>
  </Gather>
  <Redirect>{base}/twilio/voice</Redirect>
</Response>"""
    return Response(content=twiml, media_type="application/xml")


@app.post("/twilio/gather")
async def twilio_gather_webhook(request: Request):
    """
    Twilio posts the transcribed speech here.
    We generate a persona response and return TwiML.
    """
    import json
    form = await request.form()
    speech_result = form.get("SpeechResult", "")
    print(f"[TWILIO] Scammer said: {speech_result}")

    # Generate persona response
    personas_path = Path(__file__).parent / "scambaiter_personas.json"
    with open(personas_path) as f:
        data = json.load(f)

    persona_id = _scam_caller.persona_id if _scam_caller else "confused_grandma"
    personas = {p["id"]: p for p in data["personas"]}
    persona = personas.get(persona_id, data["personas"][0])

    # Try AI response, fall back to filler phrase
    response_text = random.choice(persona["filler_phrases"])
    if _scam_caller:
        responder = AIResponder(
            use_ai=bool(os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY"))
        )
        try:
            response_text = _scam_caller._persona_response(persona, speech_result, responder)
        except Exception:
            pass

    base = os.getenv("PUBLIC_BASE_URL", "http://localhost:8000")
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say voice="alice">{response_text}</Say>
  <Gather input="speech" action="{base}/twilio/gather" method="POST"
          speechTimeout="3" timeout="15">
  </Gather>
  <Redirect>{base}/twilio/voice</Redirect>
</Response>"""
    return Response(content=twiml, media_type="application/xml")


# Serve local audio files for music mode
@app.get("/audio/{filename}")
async def serve_audio(filename: str):
    path = Path(__file__).parent / "audio" / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")
    return FileResponse(str(path), media_type="audio/mpeg")


# Run server
if __name__ == "__main__":
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))

    print(f"""
    ╔════════════════════════════════════════╗
    ║   AI Auto Caller API Server            ║
    ║   Running on http://{host}:{port}       ║
    ╚════════════════════════════════════════╝

    📱 Auto-Answer: {call_handler.auto_answer_enabled}
    🎙️  TTS Engine: {call_handler.tts.engine}
    🤖 AI Enabled: {call_handler.ai_responder.use_ai}

    API Documentation: http://{host}:{port}/docs
    """)

    uvicorn.run(app, host=host, port=port)
