# Jarvis - Offline Voice Assistant

A fully offline voice assistant with a modern GUI interface, inspired by Jarvis from Iron Man. This assistant can perform various system-level tasks through voice commands.

## Features

- Voice command recognition (offline)
- Text-to-speech responses
- Modern GUI interface (Jarvis-style, blue/black, Orbitron font)
- System control (open applications, play music)
- Date and time information
- Reminder system
- Basic conversation capabilities

## Requirements

- Python 3.8 or higher
- PyAudio (for microphone input)
- Other dependencies listed in requirements.txt

## Installation

1. Clone this repository
2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the main application:
```bash
python main.py
```

### Voice Commands

- "Open [application]" - Opens specified application
- "What time is it" - Tells current time
- "What's today's date" - Tells current date
- "Set reminder" - Sets a new reminder
- "Play music" - Plays music from default music directory
- "Stop" - Stops current action
- "Exit" - Closes the application

## Note

This is a fully offline voice assistant. All processing is done locally on your machine.

---

**UI/UX:**
- Jarvis-style, blue/black theme
- Futuristic Orbitron font
- Animated listening indicator 
