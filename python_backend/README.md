# Python Backend - AI Auto Caller

FastAPI-based backend for handling AI responses and text-to-speech generation.

## Features

- 🚀 FastAPI REST API
- 🤖 AI response generation (OpenAI, Anthropic, or predefined)
- 🎙️ Multiple TTS engines (ElevenLabs, gTTS, pyttsx3)
- 📞 Call session management
- 📊 Call history tracking

## Quick Start

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Run the server**
   ```bash
   python main.py
   ```

4. **Access API docs**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## API Endpoints

### Call Management
- `POST /api/answer-call` - Answer incoming call
- `POST /api/process-speech` - Process user speech
- `POST /api/end-call/{call_id}` - End active call
- `GET /api/active-calls` - Get active calls
- `GET /api/call-history` - Get call history

### Responses
- `GET /api/responses` - Get all responses
- `POST /api/responses` - Add custom response
- `PUT /api/responses` - Update response

### Text-to-Speech
- `POST /api/tts` - Generate speech from text
- `GET /api/voices` - List available voices

### Settings
- `GET /api/settings` - Get current settings
- `PUT /api/settings` - Update settings
- `POST /api/settings/auto-answer` - Toggle auto-answer

## Configuration

### Environment Variables

```env
# API Keys (Optional)
ELEVENLABS_API_KEY=your_key
OPENAI_API_KEY=your_key
ANTHROPIC_API_KEY=your_key

# Server
HOST=0.0.0.0
PORT=8000

# TTS
DEFAULT_TTS_ENGINE=gtts  # Options: elevenlabs, gtts, pyttsx3

# AI
AI_MODEL=gpt-3.5-turbo
MAX_RESPONSE_LENGTH=100
```

## TTS Engines

### gTTS (Default - Free)
- Requires internet connection
- Uses Google's TTS
- No API key required

### ElevenLabs (Premium)
- High-quality, natural voices
- Requires API key
- Costs money per character

### pyttsx3 (Offline)
- Works offline
- Free
- Lower quality voices

## Customizing Responses

Edit `responses.json`:

```json
{
  "greeting": "Your custom greeting",
  "custom_responses": [
    "Custom response 1",
    "Custom response 2"
  ],
  "context_responses": {
    "appointment": "Custom appointment response"
  }
}
```

## Development

### Adding a New Endpoint

```python
@app.post("/api/your-endpoint")
async def your_endpoint(data: YourModel):
    # Implementation
    return {"status": "success"}
```

### Testing

```bash
# Test with curl
curl -X POST http://localhost:8000/api/answer-call \
  -H "Content-Type: application/json" \
  -d '{"caller_number": "+1234567890"}'

# Test TTS
curl -X POST http://localhost:8000/api/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world", "engine": "gtts"}' \
  --output test.mp3
```

## Troubleshooting

### Port Already in Use
```bash
# Change port in .env or:
PORT=8001 python main.py
```

### TTS Not Working
- Check API keys in `.env`
- Verify internet connection (for gTTS, ElevenLabs)
- Install system dependencies for pyttsx3

### AI Responses Not Working
- Verify API keys are set
- Check API credit balance
- Review logs for specific errors

## License

MIT
