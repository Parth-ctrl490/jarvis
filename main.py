import os
import webbrowser
import requests
import datetime
import platform
import subprocess
import re
import random
import json
from pathlib import Path

# Optional imports with error handling
try:
    import pyttsx3
    engine = pyttsx3.init()
    TTS_AVAILABLE = True
    print("Text-to-speech module loaded (but will not be used by server for responses).")
except Exception as e:
    print(f"TTS not available: {e}")
    TTS_AVAILABLE = False

try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
    print("Speech recognition available")
except ImportError:
    print("Speech recognition not available")
    SPEECH_RECOGNITION_AVAILABLE = False

try:
    import pyjokes
    JOKES_AVAILABLE = True
except ImportError:
    print("Jokes module not available")
    JOKES_AVAILABLE = False

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    print("System utilities not available")
    PSUTIL_AVAILABLE = False

try:
    import pyautogui
    SCREENSHOT_AVAILABLE = True
except ImportError:
    print("Screenshot functionality not available")
    SCREENSHOT_AVAILABLE = False

try:
    import ecapture
    CAMERA_AVAILABLE = True
except ImportError:
    print("Camera functionality not available")
    CAMERA_AVAILABLE = False

# ==================== CONVERSATION HISTORY ====================
CONVERSATION_FILE = "conversation_history.json"

def load_conversation():
    """Load conversation history from file"""
    if os.path.exists(CONVERSATION_FILE):
        try:
            with open(CONVERSATION_FILE, 'r') as f:
                return json.load(f)
        except:
            return []
    return []

def save_conversation(conversation):
    """Save conversation history to file"""
    try:
        with open(CONVERSATION_FILE, 'w') as f:
            json.dump(conversation, f, indent=2)
    except Exception as e:
        print(f"Error saving conversation: {e}")

def clear_conversation():
    """Clear conversation history"""
    if os.path.exists(CONVERSATION_FILE):
        os.remove(CONVERSATION_FILE)
    return {"text": "Conversation history cleared. Starting fresh!"}

# ==================== AI CONVERSATION HANDLER ====================
def clean_response_for_voice(text):
    """Clean AI response to be voice-friendly"""
    # Remove markdown formatting
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)  # Bold
    text = re.sub(r'\*(.+?)\*', r'\1', text)      # Italic
    text = re.sub(r'`(.+?)`', r'\1', text)        # Code
    text = re.sub(r'#+\s+', '', text)             # Headers
    
    # Remove bullet points and list markers
    text = re.sub(r'^\s*[-*•]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)
    
    # Clean up excessive newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Remove any remaining special characters that sound weird
    text = text.replace('|', '')
    text = text.replace('---', '')
    
    return text.strip()

def get_ai_response(user_message, conversation_history):
    """
    Get AI response using Groq API (FREE with generous limits)
    """
    try:
        from groq import Groq
        
        # Get API key
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            return {
                "text": "⚠️ GROQ_API_KEY not found. Get a FREE key from https://console.groq.com",
                "action": "error"
            }
        
        client = Groq(api_key=api_key)
        
        # Build conversation history for context
        messages = [
            {
                "role": "system",
                "content": """You are ECHO, a friendly voice assistant. 

CRITICAL RULES:
1. Keep responses SHORT - maximum 3-4 sentences for simple questions
2. NO markdown, asterisks, or special formatting
3. NO bullet points or numbered lists - use natural speech
4. Sound natural when read aloud
5. Be direct and conversational
6. For complex topics, be concise but informative"""
            }
        ]
        
        # Add conversation history (last 5 exchanges)
        for entry in conversation_history[-10:]:  # Last 10 messages (5 exchanges)
            messages.append({
                "role": entry["role"],
                "content": entry["content"]
            })
        
        # Add current user message
        messages.append({
            "role": "user",
            "content": user_message
        })
        
        # Call Groq API
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",  # Fast and smart
            messages=messages,
            temperature=0.7,
            max_tokens=500,  # Limit response length
            top_p=0.9
        )
        
        ai_response = response.choices[0].message.content
        
        # Clean up formatting for voice-friendly output
        ai_response = clean_response_for_voice(ai_response)
        
        # Update conversation history
        conversation_history.append({
            "role": "user",
            "content": user_message,
            "timestamp": datetime.datetime.now().isoformat()
        })
        conversation_history.append({
            "role": "assistant",
            "content": ai_response,
            "timestamp": datetime.datetime.now().isoformat()
        })
        
        save_conversation(conversation_history)
        
        return {"text": ai_response, "action": "ai_response"}
        
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        print(f"AI Response Error: {error_msg}")
        return {"text": "I encountered an error processing your message. Please try again.", "action": "error"}

# ==================== COMMAND DETECTION ====================

def is_system_command(command):
    """
    Check if the command is a system/utility command rather than a conversation
    Returns (is_command, command_type)
    """
    command_lower = command.lower().strip()
    
    # System utility commands
    system_keywords = [
        'open google', 'open youtube', 'open chatgpt', 'open whatsapp', 
        'open github', 'open spotify', 'open gmail', 'open calculator',
        'play music', 'play ',
        'screenshot', 'take picture', 'photo',
        'time', 'date',
        'weather',
        'battery',
        'system info', 'system status',
        'create file', 'read file',
        'note ', 'list notes', 'show notes',
        'remind me', 'list reminders', 'show reminders',
        'timer', 'set timer',
        'convert', 'calculate', 'what is',
        'define', 'meaning of',
        'joke', 'funny',
        'search', 'wikipedia',
        'clear conversation', 'reset chat',
        'help',
        'exit', 'quit', 'goodbye', 'bye'
    ]
    
    for keyword in system_keywords:
        if keyword in command_lower:
            return True, keyword
    
    return False, None

# ==================== ADVANCED FEATURES (keeping existing functions) ====================

def get_system_info():
    if not PSUTIL_AVAILABLE:
        return {"text": "System monitoring not available."}
    
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        
        memory = psutil.virtual_memory()
        memory_total = memory.total / (1024**3)
        memory_used = memory.used / (1024**3)
        memory_percent = memory.percent
        
        disk = psutil.disk_usage('/')
        disk_total = disk.total / (1024**3)
        disk_used = disk.used / (1024**3)
        disk_percent = disk.percent
        
        response = (
            f"System Information:\n"
            f"CPU: {cpu_percent}% usage ({cpu_count} cores)\n"
            f"RAM: {memory_used:.1f}GB / {memory_total:.1f}GB ({memory_percent}%)\n"
            f"Disk: {disk_used:.1f}GB / {disk_total:.1f}GB ({disk_percent}%)\n"
            f"OS: {platform.system()} {platform.release()}"
        )
        return {"text": response}
    except Exception as e:
        return {"text": f"Error getting system info: {str(e)}"}

def create_file(command):
    try:
        match = re.search(r'create file\s+(\S+)\s+with\s+(.+)', command, re.IGNORECASE)
        if not match:
            return {"text": "Usage: create file <filename> with <content>"}
        
        filename = match.group(1)
        content = match.group(2)
        
        docs_folder = Path.home() / "ECHO_Files"
        docs_folder.mkdir(exist_ok=True)
        
        filepath = docs_folder / filename
        with open(filepath, 'w') as f:
            f.write(content)
        
        response = f"File created successfully: {filepath}"
        return {"text": response}
    except Exception as e:
        return {"text": f"Error creating file: {str(e)}"}

def read_file(command):
    try:
        match = re.search(r'read file\s+(\S+)', command, re.IGNORECASE)
        if not match:
            return {"text": "Usage: read file <filename>"}
        
        filename = match.group(1)
        docs_folder = Path.home() / "ECHO_Files"
        filepath = docs_folder / filename
        
        if not filepath.exists():
            return {"text": f"File not found: {filename}"}
        
        with open(filepath, 'r') as f:
            content = f.read()
        
        response = f"Content of {filename}:\n{content}"
        return {"text": response}
    except Exception as e:
        return {"text": f"Error reading file: {str(e)}"}

NOTES_FILE = "echo_notes.json"

def add_note(command):
    try:
        note_text = command.replace("note", "", 1).strip()
        if not note_text:
            return {"text": "Please provide note content."}
        
        notes = []
        if os.path.exists(NOTES_FILE):
            with open(NOTES_FILE, 'r') as f:
                notes = json.load(f)
        
        note = {
            "id": len(notes) + 1,
            "text": note_text,
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        notes.append(note)
        
        with open(NOTES_FILE, 'w') as f:
            json.dump(notes, f, indent=2)
        
        response = f"Note added: '{note_text}'"
        return {"text": response}
    except Exception as e:
        return {"text": f"Error adding note: {str(e)}"}

def list_notes():
    try:
        if not os.path.exists(NOTES_FILE):
            return {"text": "You have no notes yet."}
        
        with open(NOTES_FILE, 'r') as f:
            notes = json.load(f)
        
        if not notes:
            return {"text": "You have no notes yet."}
        
        response = "Your notes:\n"
        for note in notes[-5:]:
            time_str = datetime.datetime.fromisoformat(note['timestamp']).strftime("%m/%d %I:%M %p")
            response += f"{note['id']}. {note['text']} ({time_str})\n"
        
        return {"text": response}
    except Exception as e:
        return {"text": f"Error listing notes: {str(e)}"}

def convert_currency(command):
    try:
        match = re.search(r'(\d+(?:\.\d+)?)\s*(\w+)\s+to\s+(\w+)', command, re.IGNORECASE)
        if not match:
            return {"text": "Usage: convert <amount> <from_currency> to <to_currency>"}
        
        amount = float(match.group(1))
        from_curr = match.group(2).upper()
        to_curr = match.group(3).upper()
        
        currency_map = {
            'DOLLAR': 'USD', 'DOLLARS': 'USD',
            'RUPEE': 'INR', 'RUPEES': 'INR',
            'EURO': 'EUR', 'EUROS': 'EUR',
            'POUND': 'GBP', 'POUNDS': 'GBP',
            'YEN': 'JPY'
        }
        
        from_curr = currency_map.get(from_curr, from_curr)
        to_curr = currency_map.get(to_curr, to_curr)
        
        url = f"https://api.exchangerate-api.com/v4/latest/{from_curr}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            rate = data['rates'].get(to_curr)
            if rate:
                result = amount * rate
                response_text = f"{amount} {from_curr} = {result:.2f} {to_curr}"
                return {"text": response_text}
            else:
                return {"text": f"Currency {to_curr} not found."}
        else:
            return {"text": "Currency conversion service unavailable."}
    except Exception as e:
        return {"text": f"Currency conversion error: {str(e)}"}

def convert_unit(command):
    try:
        match = re.search(r'(\d+(?:\.\d+)?)\s*(\w+)\s+to\s+(\w+)', command, re.IGNORECASE)
        if not match:
            return {"text": "Usage: convert <amount> <from_unit> to <to_unit>"}
        
        amount = float(match.group(1))
        from_unit = match.group(2).lower()
        to_unit = match.group(3).lower()
        
        distance_conversions = {
            ('km', 'miles'): 0.621371,
            ('miles', 'km'): 1.60934,
            ('m', 'feet'): 3.28084,
            ('feet', 'm'): 0.3048,
            ('cm', 'inches'): 0.393701,
            ('inches', 'cm'): 2.54
        }
        
        if from_unit in ['celsius', 'c'] and to_unit in ['fahrenheit', 'f']:
            result = (amount * 9/5) + 32
            return {"text": f"{amount}°C = {result:.1f}°F"}
        elif from_unit in ['fahrenheit', 'f'] and to_unit in ['celsius', 'c']:
            result = (amount - 32) * 5/9
            return {"text": f"{amount}°F = {result:.1f}°C"}
        
        conversion_key = (from_unit, to_unit)
        if conversion_key in distance_conversions:
            result = amount * distance_conversions[conversion_key]
            return {"text": f"{amount} {from_unit} = {result:.2f} {to_unit}"}
        
        return {"text": f"Conversion from {from_unit} to {to_unit} not supported."}
    except Exception as e:
        return {"text": f"Unit conversion error: {str(e)}"}

def get_quote():
    quotes = [
        "The only way to do great work is to love what you do. - Steve Jobs",
        "Believe you can and you're halfway there. - Theodore Roosevelt",
        "Success is not final, failure is not fatal: it is the courage to continue that counts. - Winston Churchill",
        "The future belongs to those who believe in the beauty of their dreams. - Eleanor Roosevelt",
        "It does not matter how slowly you go as long as you do not stop. - Confucius",
        "Everything you've ever wanted is on the other side of fear. - George Addair",
    ]
    
    quote = random.choice(quotes)
    return {"text": quote}

def define_word(command):
    try:
        word = command.replace('define', '').replace('what is the meaning of', '').replace('meaning of', '').strip()
        
        if not word:
            return {"text": "Please specify a word to define."}
        
        url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()[0]
            meaning = data['meanings'][0]
            definition = meaning['definitions'][0]['definition']
            part_of_speech = meaning['partOfSpeech']
            
            result = f"{word.capitalize()} ({part_of_speech}): {definition}"
            return {"text": result}
        else:
            return {"text": f"Could not find definition for '{word}'."}
    except Exception as e:
        return {"text": f"Definition lookup error: {str(e)}"}

# ==================== EXISTING FUNCTIONS ====================

def tell_time():
    try:
        now = datetime.datetime.now()
        current_time = now.strftime("%I:%M %p")
        response = f"The time is {current_time}."
        return {"text": response}
    except Exception as e:
        error_msg = f"Error getting time: {str(e)}"
        return {"text": error_msg}

def tell_date():
    try:
        now = datetime.datetime.now()
        current_date = now.strftime("%A, %B %d, %Y")
        response = f"Today's date is {current_date}."
        return {"text": response}
    except Exception as e:
        error_msg = f"Error getting date: {str(e)}"
        return {"text": error_msg}

music = {
    "stealth": "https://www.youtube.com/watch?v=U47Tr9BB_wE",
    "march": "https://www.youtube.com/watch?v=Xqeq4b5u_Xw",
    "skyfall": "https://www.youtube.com/watch?v=DeumyOzKqgI",
    "believer": "https://www.youtube.com/watch?v=7wtfhZwyrcc",
    "shape of you": "https://www.youtube.com/watch?v=JGwWNGJdvx8",
    "lecture": "https://www.youtube.com/watch?v=ZOhUXDe1Xr0&list=PL5Dqs90qDljVjbp18F1uw8cXgOobTOFGf"
}

def play_music(track_name):
    try:
        track_name = track_name.lower().strip()
        if track_name in music:
            response = f"Opening {track_name} on YouTube..."
            webbrowser.open(music[track_name])
            return {"text": response, "action": "music_played"}
        else:
            available = ", ".join(music.keys())
            response = f"Track not found. Available tracks: {available}"
            return {"text": response}
    except Exception as e:
        error_msg = f"Error playing music: {str(e)}"
        return {"text": error_msg}

def google_search(query):
    try:
        search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        webbrowser.open(search_url)
        response = f"Opening Google search for: {query}"
        return {"text": response, "action": "web_opened"}
    except Exception as e:
        error_msg = f"Error opening search: {str(e)}"
        return {"text": error_msg}

def get_weather():
    try:
        city_name = "Kanpur"
        api_key = os.getenv("WEATHER_API_KEY", "e978b3f1a04094cec994b3ad2757ece7")
        base_url = "http://api.openweathermap.org/data/2.5/weather?"
        complete_url = f"{base_url}q={city_name}&appid={api_key}&units=metric"

        response = requests.get(complete_url, timeout=10)
        data = response.json()

        if data.get('cod') == 200:
            main_data = data['main']
            wind_data = data.get('wind', {})
            weather_data = data['weather'][0]

            temperature = main_data['temp']
            pressure = main_data['pressure']
            humidity = main_data['humidity']
            weather_description = weather_data['description']
            wind_speed = wind_data.get('speed', 0)

            weather_report = (
                f"Weather in {city_name}: {temperature}°C with {weather_description}. "
                f"Humidity: {humidity}%, Pressure: {pressure} hPa, Wind: {wind_speed} m/s."
            )
            return {"text": weather_report}
        else:
            error_message = data.get('message', 'Weather service unavailable')
            response = f"Weather error: {error_message}"
            return {"text": response}
    except Exception as e:
        error_msg = f"Weather error: {str(e)}"
        return {"text": error_msg}

def get_article():
    try:
        webbrowser.open("https://news.google.com")
        response = "Opening Google News for latest articles."
        return {"text": response, "action": "web_opened"}
    except Exception as e:
        error_msg = f"Error opening news: {str(e)}"
        return {"text": error_msg}

def battery_status():
    if not PSUTIL_AVAILABLE:
        response = "Battery monitoring not available on this system."
        return {"text": response}
    
    try:
        battery = psutil.sensors_battery()
        if battery:
            percent = battery.percent
            charging = "charging" if battery.power_plugged else "not charging"
            response = f"Battery: {percent}% and {charging}."
            return {"text": response}
        else:
            response = "Battery information not available."
            return {"text": response}
    except Exception as e:
        error_msg = f"Battery error: {str(e)}"
        return {"text": error_msg}

def safe_calculate(expression):
    try:
        expression = re.sub(r'\b(calculate|what is)\b', '', expression, flags=re.IGNORECASE).strip()
        math_pattern = re.compile(r'^[\s0-9+\-*/.()]+$')
        if not expression or not math_pattern.match(expression):
            return "Invalid mathematical expression"
        result = eval(expression, {"__builtins__": {}}, {})
        return str(result)
    except ZeroDivisionError:
        return "Error: Division by zero"
    except Exception as e:
        return f"Calculation error: {str(e)}"

def open_application(app_name):
    try:
        system = platform.system().lower()
        
        if app_name == "calculator":
            if system == "windows":
                subprocess.run(['calc'], check=True)
            elif system == "darwin":
                subprocess.run(['open', '-a', 'Calculator'], check=True)
            else:
                subprocess.run(['gnome-calculator'], check=True)
            return "Calculator opened successfully"
        else:
            return f"Application '{app_name}' not supported"
    except Exception as e:
        return f"Error opening {app_name}: {str(e)}"

def take_screenshot():
    if not SCREENSHOT_AVAILABLE:
        response = "Screenshot functionality not available."
        return {"text": response}
    
    try:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{timestamp}.png"
        filepath = os.path.join("captures", filename)
        
        os.makedirs("captures", exist_ok=True)
        
        screenshot = pyautogui.screenshot()
        screenshot.save(filepath)
        final_response = f"Screenshot saved successfully"
        return {
            "text": final_response, 
            "action": "screenshot_taken",
            "image_url": f"/captures/{filename}",
            "filename": filename
        }
    except Exception as e:
        error_msg = f"Screenshot error: {str(e)}"
        return {"text": error_msg}

def take_picture():
    if not CAMERA_AVAILABLE:
        response = "Camera functionality not available."
        return {"text": response}
    
    try:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"photo_{timestamp}.jpg"
        filepath = os.path.join("captures", filename)
        
        os.makedirs("captures", exist_ok=True)
        
        ecapture.capture(0, "ECHO Assistant", filepath)
        final_response = "Picture captured successfully"
        return {
            "text": final_response, 
            "action": "picture_taken",
            "image_url": f"/captures/{filename}",
            "filename": filename
        }
    except Exception as e:
        error_msg = f"Camera error: {str(e)}"
        return {"text": error_msg}

def get_joke():
    if not JOKES_AVAILABLE:
        jokes = [
            "Why don't scientists trust atoms? Because they make up everything!",
            "Why did the computer go to the doctor? Because it had a virus!",
            "Why don't robots ever panic? Because they have nerves of steel!"
        ]
        joke = random.choice(jokes)
    else:
        try:
            joke = pyjokes.get_joke()
        except:
            joke = "Why don't scientists trust atoms? Because they make up everything!"
    
    return {"text": joke}

def execute_command(command):
    """Main command execution function with AI conversation support"""
    if not command or not command.strip():
        response = "Please provide a command."
        return {"text": response}
    
    command = command.strip()
    print(f"Processing command: {command}")
    
    try:
        # Check if it's a system command
        is_command, command_type = is_system_command(command)
        
        # Handle clear conversation
        if 'clear conversation' in command.lower() or 'reset chat' in command.lower():
            return clear_conversation()
        
        # If it's a system command, handle it with existing functions
        if is_command:
            command_lower = command.lower()
            
            # Time and Date
            if any(word in command_lower for word in ['time', 'clock']):
                return tell_time()
            
            elif any(word in command_lower for word in ['date', 'today']) and 'update' not in command_lower:
                return tell_date()
            
            # Music
            elif 'play' in command_lower:
                track_name = command.replace('play', '').strip()
                return play_music(track_name)
            
            # Web Applications
            elif 'open google' in command_lower:
                webbrowser.open("https://www.google.co.in/")
                response = "Opening Google for you..."
                return {"text": response, "action": "web_opened"}
            
            elif 'open youtube' in command_lower:
                webbrowser.open("https://www.youtube.com/")
                response = "Opening YouTube..."
                return {"text": response, "action": "web_opened"}
            
            elif 'open chatgpt' in command_lower:
                webbrowser.open("https://chat.openai.com/")
                response = "Opening ChatGPT..."
                return {"text": response, "action": "web_opened"}
            
            elif 'open whatsapp' in command_lower:
                webbrowser.open("https://web.whatsapp.com/")
                response = "Opening WhatsApp Web..."
                return {"text": response, "action": "web_opened"}
            
            elif 'open github' in command_lower:
                webbrowser.open("https://github.com/")
                response = "Opening GitHub..."
                return {"text": response, "action": "web_opened"}
            
            elif 'open spotify' in command_lower:
                webbrowser.open("https://open.spotify.com/")
                response = "Opening Spotify..."
                return {"text": response, "action": "web_opened"}
            
            elif 'open gmail' in command_lower:
                webbrowser.open("https://mail.google.com/")
                response = "Opening Gmail..."
                return {"text": response, "action": "web_opened"}
            
            # Calculator
            elif 'open calculator' in command_lower:
                result = open_application("calculator")
                return {"text": result}
            
            # Calculations
            elif any(phrase in command_lower for phrase in ['calculate', 'what is', 'compute']) and any(char in command for char in '0123456789+-*/.'):
                result = safe_calculate(command)
                response = f"The result is: {result}"
                return {"text": response}
            
            # Search
            elif 'search' in command_lower:
                search_query = command.replace('wikipedia', '').replace('wiki', '').replace('search', '').strip()
                if search_query:
                    return google_search(search_query)
                else:
                    response = "Please specify what you want to search for."
                    return {"text": response}
            
            # Weather
            elif 'weather' in command_lower:
                return get_weather()
            
            # Battery
            elif 'battery' in command_lower:
                return battery_status()
            
            # Jokes
            elif any(word in command_lower for word in ['joke', 'funny', 'humor']):
                return get_joke()
            
            # Screenshots and Pictures
            elif 'screenshot' in command_lower:
                return take_screenshot()
            
            elif 'picture' in command_lower or 'photo' in command_lower:
                return take_picture()
            
            # News/Articles
            elif any(word in command_lower for word in ['news', 'article']):
                return get_article()
            
            # System Information
            elif 'system info' in command_lower or 'system status' in command_lower:
                return get_system_info()
            
            # File Operations
            elif 'create file' in command_lower:
                return create_file(command)
            
            elif 'read file' in command_lower:
                return read_file(command)
            
            # Notes
            elif command_lower.startswith('note '):
                return add_note(command)
            
            elif 'list notes' in command_lower or 'show notes' in command_lower or 'my notes' in command_lower:
                return list_notes()
            
            # Currency Conversion
            elif 'convert' in command_lower and any(word in command_lower for word in ['usd', 'inr', 'eur', 'gbp', 'dollar', 'rupee', 'euro', 'pound']):
                return convert_currency(command)
            
            # Unit Conversion
            elif 'convert' in command_lower and any(word in command_lower for word in ['km', 'miles', 'celsius', 'fahrenheit', 'feet', 'meter']):
                return convert_unit(command)
            
            # Quotes
            elif 'quote' in command_lower or 'motivate me' in command_lower or 'inspire me' in command_lower:
                return get_quote()
            
            # Dictionary
            elif 'define' in command_lower or 'meaning of' in command_lower:
                return define_word(command)
            
            # System commands
            elif any(word in command_lower for word in ['exit', 'quit', 'goodbye', 'bye']):
                response = "Goodbye! ECHO signing off. Have a wonderful day!"
                return {"text": response, "action": "exit"}
            
            # Help
            elif 'help' in command_lower:
                response = (
                    "I can help you with:\n\n"
                    "💬 CONVERSATIONAL AI:\n"
                    "- Ask me anything! I can answer questions, help with problems, write content, explain concepts, and have natural conversations.\n"
                    "- Just chat naturally - I remember our conversation context.\n\n"
                    "🛠️ SYSTEM COMMANDS:\n"
                    "⏰ Time & Date: 'time', 'date'\n"
                    "🎵 Music: 'play [song name]'\n"
                    "🌐 Web: 'open google/youtube/github/spotify/gmail'\n"
                    "🔍 Search: 'search [query]'\n"
                    "🌤️ Weather: 'weather'\n"
                    "🔋 Battery: 'battery status'\n"
                    "📸 Capture: 'screenshot', 'take picture'\n"
                    "🧮 Calculate: 'calculate 2+2', 'what is 10*5'\n"
                    "📝 Notes: 'note [text]', 'list notes'\n"
                    "💱 Convert: 'convert 100 usd to inr'\n"
                    "📖 Dictionary: 'define [word]'\n"
                    "💻 System: 'system info'\n"
                    "📁 Files: 'create file [name] with [content]'\n"
                    "😂 Jokes: 'tell me a joke'\n"
                    "🔄 Clear Chat: 'clear conversation'"
                )
                return {"text": response}
        
        # If not a system command, use AI conversation
        conversation_history = load_conversation()
        return get_ai_response(command, conversation_history)
            
    except Exception as e:
        error_msg = f"An error occurred: {str(e)}"
        print(f"Error in execute_command: {error_msg}")
        return {"text": error_msg}

# Standalone mode for testing
if __name__ == "__main__":
    def speak(text):
        """Text-to-speech function for standalone mode"""
        if TTS_AVAILABLE:
            try:
                engine.say(text)
                engine.runAndWait()
                print(f"ECHO (Speaking): {text}")
            except Exception as e:
                print(f"TTS Error: {e}")
                print(f"ECHO: {text}")
        else:
            print(f"ECHO: {text}")

    def take_command():
        """Voice command recognition for standalone mode"""
        if not SPEECH_RECOGNITION_AVAILABLE:
            print("Voice recognition not available. Please type your command.")
            return input("You: ")
        
        try:
            recognizer = sr.Recognizer()
            with sr.Microphone() as source:
                print("Listening...")
                recognizer.adjust_for_ambient_noise(source, duration=1)
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
                
            command = recognizer.recognize_google(audio)
            print(f"Voice Command: {command}")
            return command.lower()
        except Exception:
            print("Didn't catch that. Please type your command.")
            return input("You: ")
            
    print("ECHO AI Assistant - Standalone Mode")
    print("Now with conversational AI! Ask me anything or use system commands.")
    speak("Hello! I'm ECHO with enhanced conversational abilities. How can I assist you today?")
    
    while True:
        try:
            command = take_command()
            if 'exit' in command.lower():
                speak("Goodbye!")
                break
            result_dict = execute_command(command)
            speak(result_dict.get('text', 'An unknown error occurred.'))
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break

