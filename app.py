# app.py (The Flask Web Server)

from flask import Flask, request, jsonify, render_template
import main # Imports the logic from your main.py file

# Check if pyttsx3 is available for a status check
try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False

app = Flask(__name__, template_folder='templates')

@app.route('/')
def index():
    """Serves the main HTML page."""
    return render_template('index.html')

@app.route('/status')
def status():
    """A status endpoint for the UI to check the connection."""
    return jsonify({
        'status': 'online',
        'tts_available': TTS_AVAILABLE
    })

@app.route('/command', methods=['POST'])
def handle_command():
    """Receives commands from the UI and executes them."""
    data = request.json
    command = data.get('command', '')

    if not command:
        return jsonify({'text': "Please provide a command."})

    # Call the core logic function from main.py
    response_data = main.execute_command(command)
    
    # Return the dictionary response as JSON to the UI
    return jsonify(response_data)

if __name__ == '__main__':
    # Use host='0.0.0.0' to make it accessible on your local network
    app.run(host='0.0.0.0', port=5000, debug=True)