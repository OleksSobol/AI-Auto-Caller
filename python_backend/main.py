"""
FastAPI Server for AI Auto Caller
Provides REST API for call handling, TTS, and AI responses
"""

import os
import uuid
from typing import Optional, List
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from call_handler import CallHandler
from ai_responder import AIResponder
from tts_engine import TTSEngine

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="AI Auto Caller API",
    description="Automatic phone call answering with AI-powered responses",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize call handler
call_handler = CallHandler(
    tts_engine=os.getenv("DEFAULT_TTS_ENGINE", "gtts"),
    use_ai=bool(os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY"))
)


# Pydantic models
class IncomingCall(BaseModel):
    call_id: Optional[str] = None
    caller_number: str


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
    """
    Handle incoming call

    Auto-answers the call and sends greeting
    """
    try:
        # Generate call ID if not provided
        if not call.call_id:
            call.call_id = f"call_{uuid.uuid4().hex[:8]}"

        result = await call_handler.handle_incoming_call(
            call.call_id,
            call.caller_number
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/process-speech")
async def process_speech(speech: UserSpeech):
    """
    Process user's speech and generate AI response

    Receives transcribed speech, generates response, and creates TTS audio
    """
    try:
        result = await call_handler.process_user_speech(
            speech.call_id,
            speech.text
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/end-call/{call_id}")
async def end_call(call_id: str):
    """End an active call"""
    try:
        result = await call_handler.end_call(call_id)
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
        "total_calls_processed": len(call_handler.call_history)
    }


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
