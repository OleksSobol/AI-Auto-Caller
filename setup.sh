#!/bin/bash

echo "========================================="
echo "AI Auto Caller - Setup Script"
echo "========================================="
echo ""

# Check Python installation
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

echo "✅ Python 3 detected: $(python3 --version)"

# Check Flutter installation
if ! command -v flutter &> /dev/null; then
    echo "⚠️  Flutter is not installed. You'll need to install it separately."
    echo "   Visit: https://docs.flutter.dev/get-started/install"
else
    echo "✅ Flutter detected: $(flutter --version | head -n 1)"
fi

echo ""
echo "========================================="
echo "Setting up Python Backend..."
echo "========================================="

cd python_backend

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit python_backend/.env and add your API keys!"
fi

cd ..

echo ""
echo "========================================="
echo "Setting up Flutter App..."
echo "========================================="

if command -v flutter &> /dev/null; then
    cd flutter_app

    echo "📥 Installing Flutter dependencies..."
    flutter pub get

    echo "🔧 Running Flutter doctor..."
    flutter doctor

    cd ..
else
    echo "⚠️  Skipping Flutter setup (not installed)"
fi

echo ""
echo "========================================="
echo "Setup Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Edit python_backend/.env with your API keys (optional)"
echo "2. Start the Python backend:"
echo "   cd python_backend"
echo "   source venv/bin/activate"
echo "   python main.py"
echo ""
echo "3. In a new terminal, run the Flutter app:"
echo "   cd flutter_app"
echo "   flutter run"
echo ""
echo "📖 Read README.md for more information"
echo ""
