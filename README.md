# Echo AI – Advanced Voice-Driven Personal Assistant

A multilingual AI-powered voice assistant with a microservices-style Flask REST API backend and React.js frontend — supporting real-time voice commands in English & Hindi.

---

## Overview

Echo AI is a full-stack voice assistant that allows users to interact with an AI using natural speech in **English and Hindi**. It automates system tasks, answers queries, and logs all interactions through a web interface powered by WebSockets for real-time communication.

---

## Features

- Multilingual voice recognition — English and Hindi
- OpenAI API integration for intelligent, context-aware responses
- Real-time WebSocket-based low-latency communication
- Interaction logging stored in MongoDB via REST APIs
- System task automation — open apps, search web via voice
- Text-to-speech output using pyttsx3
- React.js web interface for browser-based interaction

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, Flask, REST APIs |
| Frontend | React.js, HTML5, CSS3 |
| AI/ML | TensorFlow, OpenAI API, SpeechRecognition |
| Database | MongoDB |
| Communication | WebSockets |
| TTS | pyttsx3 |

---

## Project Structure

```
jarvis/
├── app.py              # Flask REST API backend & WebSocket server
├── main.py             # Core voice assistant logic
├── install_audio.py    # Audio dependencies installer
├── templates/          # HTML templates for web interface
├── req.txt             # Python dependencies
└── echo_assistant.log  # Interaction logs
```

---

## Getting Started

### Prerequisites
- Python 3.8+
- MongoDB running locally or MongoDB Atlas URI
- OpenAI API key

### Installation

1. Clone the repository
```bash
git clone https://github.com/Parth-ctrl490/jarvis.git
cd jarvis
```

2. Install Python dependencies
```bash
pip install -r req.txt
```

3. Install audio dependencies
```bash
python install_audio.py
```

4. Set up environment variables
```bash
OPENAI_API_KEY=your_openai_api_key
MONGO_URI=your_mongodb_connection_string
```

5. Run the Flask backend
```bash
python app.py
```

6. Open in browser
```
http://localhost:5000
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Serve web interface |
| POST | `/api/command` | Process voice command |
| GET | `/api/logs` | Retrieve interaction logs |
| WebSocket | `/ws` | Real-time voice stream |

---

## Architecture

```
User Voice Input
      ↓
React.js Frontend (WebSocket)
      ↓
Flask REST API Backend
      ↓
SpeechRecognition  →  Converts speech to text
OpenAI API         →  Generates intelligent response
TensorFlow         →  Speech processing pipeline
pyttsx3            →  Text to speech output
      ↓
MongoDB (Interaction Logs)
```

---

## Dependencies

```
flask
flask-socketio
openai
speechrecognition
pyttsx3
tensorflow
pymongo
python-dotenv
```

---

## Author

**Parth Shukla**
- GitHub: https://github.com/Parth-ctrl490
- LinkedIn: https://www.linkedin.com/in/parth-shukla-0b5a57287
