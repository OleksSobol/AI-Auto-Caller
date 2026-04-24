"""
IVR Auto-Navigator
Detects and automatically navigates phone menu prompts using DTMF tones
"""

import re
import asyncio
from typing import Optional


# Common IVR prompt patterns and their best responses
IVR_RULES = [
    # Language selection
    (r"press\s+1\s+for\s+english|english.*press\s+1", "1"),
    (r"para\s+espa[ñn]ol.*press\s+2|press\s+2.*espa[ñn]ol", "1"),

    # Main menu - always try to reach a human
    (r"speak\s+to\s+a\s+(live\s+)?(agent|representative|operator|person)|press\s+0", "0"),
    (r"press\s+1\s+to\s+(speak|talk|connect)", "1"),
    (r"press\s+[0-9]\s+for.{0,30}(billing|account|service|help|support)", None),  # pick first match

    # Hold / wait
    (r"your call (is|will be) (answered|connected)|please hold|wait", None),  # wait, no key

    # Confirmation prompts
    (r"press\s+1\s+to\s+confirm|confirm.*press\s+1", "1"),
    (r"press\s+[#*1]\s+to\s+(continue|proceed)", "1"),

    # Survey / feedback - skip
    (r"press\s+1\s+to\s+take\s+a\s+survey|feedback\s+survey", "2"),

    # Generic "press any key"
    (r"press\s+any\s+key", "1"),
]


class IVRNavigator:
    """Automatically navigates IVR phone menus"""

    def __init__(self):
        self.history: list[str] = []   # keys pressed so far
        self.attempts = 0

    def decide(self, prompt_text: str) -> Optional[str]:
        """
        Analyse spoken IVR prompt and decide which key to press.

        Args:
            prompt_text: Transcribed or synthesized IVR speech

        Returns:
            DTMF key to press, or None if we should just wait
        """
        text = prompt_text.lower()

        # Walk rules in order; first match wins
        for pattern, key in IVR_RULES:
            if re.search(pattern, text):
                if key is not None:
                    self.history.append(key)
                return key

        # Fall-back: if we hear a digit mentioned alone, press it
        m = re.search(r"press\s+([0-9#*])", text)
        if m:
            key = m.group(1)
            self.history.append(key)
            return key

        self.attempts += 1
        # After 3 failed attempts just press 0 to reach a human
        if self.attempts >= 3:
            self.history.append("0")
            return "0"

        return None

    def reset(self):
        self.history.clear()
        self.attempts = 0


# Stand-alone smoke-test
if __name__ == "__main__":
    nav = IVRNavigator()
    samples = [
        "Thank you for calling. Press 1 for English.",
        "For billing press 1, for technical support press 2.",
        "All agents are busy. Please hold.",
        "Press 1 to speak with a live agent.",
        "Press 1 to confirm your appointment.",
    ]
    for s in samples:
        key = nav.decide(s)
        print(f"Prompt : {s!r}")
        print(f"Action : press {key!r}\n")
