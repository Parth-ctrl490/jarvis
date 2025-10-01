from flask import Flask, request, jsonify, render_template, send_from_directory
import main 
import os

# Check if pyttsx3 is available for a status check
try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False

app = Flask(__name__, template_folder='templates')

# Create a directory for captured images if it doesn't exist
CAPTURE_FOLDER = 'captures'
if not os.path.exists(CAPTURE_FOLDER):
    os.makedirs(CAPTURE_FOLDER)

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

@app.route('/captures/<filename>')
def serve_capture(filename):
    """Serve captured images and screenshots."""
    return send_from_directory(CAPTURE_FOLDER, filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
