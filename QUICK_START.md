# Quick Start Guide - AI Auto Caller

Get up and running in 5 minutes!

## Prerequisites

- **Python 3.8+** - [Download here](https://www.python.org/downloads/)
- **Flutter 3.0+** - [Install guide](https://docs.flutter.dev/get-started/install)
- **Android device or emulator** (for testing)

## Installation

### Option 1: Automated Setup (Linux/Mac)

```bash
# Clone the repository
git clone https://github.com/yourusername/AI-Auto-Caller.git
cd AI-Auto-Caller

# Run setup script
chmod +x setup.sh
./setup.sh
```

### Option 2: Manual Setup

#### Python Backend

```bash
cd python_backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure (optional - for AI features)
cp .env.example .env
nano .env  # Add your API keys
```

#### Flutter App

```bash
cd flutter_app

# Install dependencies
flutter pub get

# Check Flutter setup
flutter doctor
```

## Running the App

### 1. Start Python Backend

```bash
cd python_backend
source venv/bin/activate
python main.py
```

You should see:
```
╔════════════════════════════════════════╗
║   AI Auto Caller API Server            ║
║   Running on http://0.0.0.0:8000       ║
╚════════════════════════════════════════╝
```

Visit http://localhost:8000/docs to see API documentation.

### 2. Start Flutter App

In a **new terminal**:

```bash
cd flutter_app
flutter run
```

Select your device when prompted.

## First Steps

1. **Grant Permissions**
   - The app will request phone and microphone permissions
   - Grant all permissions for full functionality

2. **Enable Auto-Answer**
   - Toggle the "Auto-Answer" switch on the home screen
   - The app will now automatically answer calls

3. **Customize Responses**
   - Tap "Manage Responses" to edit AI responses
   - Add custom responses for different scenarios

4. **Test It Out**
   - Make a test call to your phone
   - The app should auto-answer and respond with AI

## Configuration

### Using Free TTS (Default)

The app uses **gTTS** (Google Text-to-Speech) by default - **no API keys needed**!

### Upgrading to Premium TTS

For better voice quality, use **ElevenLabs**:

1. Sign up at [ElevenLabs](https://elevenlabs.io/)
2. Get your API key
3. Edit `python_backend/.env`:
   ```env
   ELEVENLABS_API_KEY=your_key_here
   DEFAULT_TTS_ENGINE=elevenlabs
   ```
4. Restart the backend

### Enabling AI Responses

For dynamic, context-aware responses:

1. Get an API key from:
   - [OpenAI](https://platform.openai.com/) (GPT-3.5/4)
   - [Anthropic](https://www.anthropic.com/) (Claude)

2. Edit `python_backend/.env`:
   ```env
   OPENAI_API_KEY=your_key_here
   # OR
   ANTHROPIC_API_KEY=your_key_here
   ```

3. Enable AI in the app settings

## Troubleshooting

### Backend won't start
```bash
# Check Python version
python3 --version  # Should be 3.8+

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Flutter app can't connect
```bash
# Update backend URL in flutter_app/lib/services/api_service.dart
# Change from localhost to your computer's IP address
final String baseUrl = 'http://192.168.1.XXX:8000';
```

### Permissions not working
- Go to Android Settings > Apps > AI Auto Caller > Permissions
- Manually enable Phone and Microphone permissions

### TTS not working
```bash
# Test TTS directly
cd python_backend
python tts_engine.py
```

## Next Steps

- 📖 Read the full [README.md](README.md)
- ⚙️ Explore [Settings](flutter_app/lib/screens/settings_screen.dart)
- 🎨 Customize [Responses](python_backend/responses.json)
- 🤝 Check [CONTRIBUTING.md](CONTRIBUTING.md) to contribute

## Need Help?

- 📧 Open an issue on GitHub
- 💬 Check the documentation
- 🐛 Report bugs with logs and screenshots

---

**Happy calling! 📞🤖**
