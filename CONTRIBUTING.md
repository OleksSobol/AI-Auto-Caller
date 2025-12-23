# Contributing to AI Auto Caller

Thank you for your interest in contributing to AI Auto Caller! This document provides guidelines and instructions for contributing.

## Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/AI-Auto-Caller.git
   cd AI-Auto-Caller
   ```

2. **Run the setup script**
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

3. **Configure environment**
   - Edit `python_backend/.env` with your API keys
   - Update `flutter_app/lib/services/api_service.dart` with your backend URL

## Project Structure

```
AI-Auto-Caller/
├── python_backend/       # Python FastAPI backend
│   ├── main.py          # API server
│   ├── ai_responder.py  # AI response logic
│   ├── tts_engine.py    # Text-to-speech
│   ├── call_handler.py  # Call management
│   └── responses.json   # Predefined responses
│
├── flutter_app/         # Flutter mobile app
│   ├── lib/
│   │   ├── main.dart
│   │   ├── screens/     # UI screens
│   │   ├── services/    # API & call services
│   │   └── providers/   # State management
│   └── pubspec.yaml
│
└── README.md
```

## Coding Standards

### Python
- Follow PEP 8 style guide
- Use type hints where appropriate
- Add docstrings to all functions and classes
- Keep functions focused and under 50 lines when possible

### Flutter/Dart
- Follow official Dart style guide
- Use meaningful variable names
- Keep widgets small and reusable
- Use const constructors when possible

## Adding New Features

### Adding a New Response Type

1. **Update `responses.json`**
   ```json
   {
     "your_new_response": "Response text here"
   }
   ```

2. **Add method in `ai_responder.py`**
   ```python
   def get_your_new_response(self) -> str:
       return self.responses.get("your_new_response", "Default")
   ```

### Adding a New TTS Engine

1. **Update `tts_engine.py`**
   ```python
   async def _your_engine_tts(self, text: str, output_path: Optional[str] = None):
       # Implementation here
       pass
   ```

2. **Update the engine selection**
   ```python
   if self.engine == "your_engine":
       return await self._your_engine_tts(text, output_path)
   ```

3. **Update documentation and settings UI**

## Testing

### Backend Testing
```bash
cd python_backend
source venv/bin/activate
python -m pytest tests/
```

### Flutter Testing
```bash
cd flutter_app
flutter test
```

### Manual Testing
1. Start the backend: `./run_backend.sh`
2. Run Flutter app: `cd flutter_app && flutter run`
3. Test with actual phone calls or simulated calls

## Submitting Changes

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write clean, documented code
   - Add tests if applicable
   - Update documentation

3. **Test thoroughly**
   - Run all tests
   - Test manually with the app
   - Check for any breaking changes

4. **Commit with clear messages**
   ```bash
   git commit -m "Add: New TTS engine support for Azure"
   ```

5. **Push and create a pull request**
   ```bash
   git push origin feature/your-feature-name
   ```

## Code Review Process

1. All submissions require review
2. Reviewers will check for:
   - Code quality and style
   - Test coverage
   - Documentation
   - Performance implications

## Feature Requests & Bug Reports

### Bug Reports
Include:
- Description of the bug
- Steps to reproduce
- Expected vs actual behavior
- Environment (OS, Python version, Flutter version)
- Logs/screenshots if applicable

### Feature Requests
Include:
- Clear description of the feature
- Use case and motivation
- Proposed implementation (if you have ideas)
- Any alternative solutions considered

## Questions?

Feel free to open an issue with your question or reach out to the maintainers.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
