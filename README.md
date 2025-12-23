# AI Auto Caller - Automatic Phone Call Answering App

An intelligent phone call answering application that automatically picks up calls and responds using AI-powered voice responses.

## Features

- 🤖 **Automatic Call Answering**: Automatically picks up incoming calls
- 💬 **AI-Powered Responses**: Predefined intelligent responses using AI
- 🎙️ **Text-to-Speech**: Uses ElevenLabs (premium) or free alternatives (gTTS, pyttsx3)
- ⚙️ **Customizable Responses**: Manage and configure auto-responses
- 📱 **Flutter UI**: Clean, intuitive mobile interface
- 🐍 **Python Backend**: Robust AI and TTS processing

## Architecture

```
AI-Auto-Caller/
├── flutter_app/          # Flutter mobile application
│   ├── lib/
│   │   ├── main.dart
│   │   ├── screens/
│   │   ├── services/
│   │   └── models/
│   └── pubspec.yaml
├── python_backend/       # Python AI & TTS backend
│   ├── main.py
│   ├── ai_responder.py
│   ├── tts_engine.py
│   ├── call_handler.py
│   └── requirements.txt
└── README.md
```

## Tech Stack

### Frontend
- **Flutter**: Cross-platform mobile framework
- **phone_state**: Call detection plugin
- **http**: API communication

### Backend
- **Python 3.8+**: Core backend
- **FastAPI**: REST API framework
- **ElevenLabs API**: Premium TTS (optional)
- **gTTS**: Free Google Text-to-Speech
- **pyttsx3**: Offline TTS alternative
- **OpenAI GPT**: AI response generation (or local alternatives)

## Setup Instructions

### Python Backend Setup

1. Navigate to backend directory:
```bash
cd python_backend
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure API keys in `.env`:
```env
ELEVENLABS_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here  # Optional
```

4. Run the backend:
```bash
python main.py
```

### Flutter App Setup

1. Navigate to Flutter directory:
```bash
cd flutter_app
```

2. Install dependencies:
```bash
flutter pub get
```

3. Run the app:
```bash
flutter run
```

## Configuration

### Predefined Responses

Edit `python_backend/responses.json` to customize auto-responses:

```json
{
  "greeting": "Hello! This is an automated assistant. How can I help you?",
  "unavailable": "I'm currently unavailable. Please leave a message.",
  "business_hours": "Thank you for calling. Our business hours are 9 AM to 5 PM.",
  "custom_responses": [
    "I'll get back to you shortly.",
    "Please send me a text message instead."
  ]
}
```

### TTS Options

- **ElevenLabs**: High-quality, natural voices (requires API key)
- **gTTS**: Free, Google-powered TTS (requires internet)
- **pyttsx3**: Offline TTS (no API key needed)

## Permissions Required (Android)

- `READ_PHONE_STATE`: Detect incoming calls
- `CALL_PHONE`: Answer calls automatically
- `ANSWER_PHONE_CALLS`: Auto-answer functionality
- `INTERNET`: API communication

## Usage

1. Launch the app
2. Grant necessary permissions
3. Toggle "Auto-Answer" on
4. Configure your preferred responses
5. Select TTS engine (ElevenLabs/gTTS/pyttsx3)
6. The app will automatically answer and respond to calls

## API Endpoints

- `POST /api/answer-call`: Trigger call answering
- `GET /api/responses`: Get predefined responses
- `POST /api/responses`: Add new response
- `POST /api/tts`: Generate speech from text
- `GET /api/voices`: List available voices

## License

MIT License

## Contributing

Pull requests welcome! Please read CONTRIBUTING.md first.
