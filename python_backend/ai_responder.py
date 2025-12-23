"""
AI Response Generator
Handles intelligent response generation using predefined responses and optional AI
"""

import json
import random
import re
from typing import List, Dict, Optional
from pathlib import Path


class AIResponder:
    """AI-powered response generator with fallback to predefined responses"""

    def __init__(self, responses_file: str = "responses.json", use_ai: bool = False):
        """
        Initialize AI responder

        Args:
            responses_file: Path to JSON file with predefined responses
            use_ai: Whether to use AI API for dynamic responses
        """
        self.responses_file = Path(responses_file)
        self.use_ai = use_ai
        self.responses = self._load_responses()
        self.conversation_history = []

    def _load_responses(self) -> Dict:
        """Load predefined responses from JSON file"""
        try:
            with open(self.responses_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                "greeting": "Hello! How can I help you?",
                "unavailable": "I'm currently unavailable.",
                "custom_responses": []
            }

    def save_responses(self):
        """Save responses back to JSON file"""
        with open(self.responses_file, 'w') as f:
            json.dump(self.responses, f, indent=2)

    def add_custom_response(self, response: str):
        """Add a new custom response"""
        if "custom_responses" not in self.responses:
            self.responses["custom_responses"] = []
        self.responses["custom_responses"].append(response)
        self.save_responses()

    def get_greeting(self) -> str:
        """Get greeting response"""
        return self.responses.get("greeting", "Hello! How can I help you?")

    def get_goodbye(self) -> str:
        """Get goodbye response"""
        return self.responses.get("goodbye", "Thank you for calling. Goodbye!")

    def detect_intent(self, user_input: str) -> str:
        """
        Detect user intent from input

        Args:
            user_input: User's spoken text (transcribed)

        Returns:
            Detected intent category
        """
        user_input_lower = user_input.lower()

        # Intent keywords mapping
        intents = {
            "appointment": ["appointment", "schedule", "book", "reservation"],
            "pricing": ["price", "cost", "how much", "payment", "fee"],
            "support": ["help", "support", "problem", "issue", "broken", "not working"],
            "general_inquiry": ["information", "tell me", "what", "how", "when", "where"]
        }

        # Check for intent matches
        for intent, keywords in intents.items():
            if any(keyword in user_input_lower for keyword in keywords):
                return intent

        return "general_inquiry"

    def generate_response(self, user_input: Optional[str] = None, context: str = "general") -> str:
        """
        Generate appropriate response based on user input and context

        Args:
            user_input: User's spoken text (if available)
            context: Conversation context (greeting, unavailable, etc.)

        Returns:
            Generated response text
        """
        # Add to conversation history
        if user_input:
            self.conversation_history.append({"role": "user", "content": user_input})

        # Handle specific contexts
        if context in self.responses:
            response = self.responses[context]
        elif user_input and self.use_ai:
            # Use AI for dynamic response
            response = self._generate_ai_response(user_input)
        elif user_input:
            # Use intent-based predefined response
            intent = self.detect_intent(user_input)
            response = self.responses.get("context_responses", {}).get(
                intent,
                self._get_random_custom_response()
            )
        else:
            response = self.get_greeting()

        # Add to conversation history
        self.conversation_history.append({"role": "assistant", "content": response})

        return response

    def _get_random_custom_response(self) -> str:
        """Get a random custom response"""
        custom = self.responses.get("custom_responses", [])
        if custom:
            return random.choice(custom)
        return "I understand. How else can I assist you?"

    def _generate_ai_response(self, user_input: str) -> str:
        """
        Generate AI-powered response using OpenAI or Anthropic

        Args:
            user_input: User's message

        Returns:
            AI-generated response
        """
        try:
            import os

            # Try OpenAI first
            if os.getenv("OPENAI_API_KEY"):
                return self._openai_response(user_input)
            # Try Anthropic
            elif os.getenv("ANTHROPIC_API_KEY"):
                return self._anthropic_response(user_input)
            else:
                # Fallback to predefined
                return self._get_random_custom_response()

        except Exception as e:
            print(f"AI response generation failed: {e}")
            return self._get_random_custom_response()

    def _openai_response(self, user_input: str) -> str:
        """Generate response using OpenAI"""
        try:
            from openai import OpenAI
            client = OpenAI()

            messages = [
                {"role": "system", "content": "You are a helpful phone assistant. Keep responses brief and natural, under 50 words."},
                *self.conversation_history[-5:],  # Last 5 messages
                {"role": "user", "content": user_input}
            ]

            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=100,
                temperature=0.7
            )

            return response.choices[0].message.content.strip()
        except Exception as e:
            raise Exception(f"OpenAI failed: {e}")

    def _anthropic_response(self, user_input: str) -> str:
        """Generate response using Anthropic Claude"""
        try:
            from anthropic import Anthropic
            client = Anthropic()

            # Build conversation context
            conversation = "\n".join([
                f"{msg['role']}: {msg['content']}"
                for msg in self.conversation_history[-5:]
            ])

            response = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=100,
                messages=[{
                    "role": "user",
                    "content": f"{conversation}\nuser: {user_input}\n\nRespond as a helpful phone assistant. Keep it brief and natural (under 50 words)."
                }]
            )

            return response.content[0].text.strip()
        except Exception as e:
            raise Exception(f"Anthropic failed: {e}")

    def reset_conversation(self):
        """Reset conversation history"""
        self.conversation_history = []

    def get_all_responses(self) -> Dict:
        """Get all available responses"""
        return self.responses

    def update_response(self, category: str, new_response: str):
        """Update a specific response category"""
        self.responses[category] = new_response
        self.save_responses()


# Example usage
if __name__ == "__main__":
    responder = AIResponder()

    # Test greeting
    print("Greeting:", responder.get_greeting())

    # Test intent detection
    print("\nIntent (appointment):", responder.detect_intent("I'd like to schedule an appointment"))
    print("Intent (pricing):", responder.detect_intent("How much does it cost?"))

    # Test response generation
    print("\nResponse:", responder.generate_response("I need help with my account", "general"))
