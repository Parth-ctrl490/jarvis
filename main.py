import os
import webbrowser
import requests
import datetime
import platform
import subprocess
import re

# Optional imports with error handling
try:
    import pyttsx3
    engine = pyttsx3.init()
    TTS_AVAILABLE = True
    print("Text-to-speech initialized successfully")
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

# Function to speak text
def speak(text):
    """Text-to-speech function with fallback"""
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

# Function to get current time
def tell_time():
    try:
        now = datetime.datetime.now()
        current_time = now.strftime("%I:%M %p")
        response = f"The time is {current_time}."
        speak(response)
        return {"text": response}
    except Exception as e:
        error_msg = f"Error getting time: {str(e)}"
        speak(error_msg)
        return {"text": error_msg}

# Function to get current date
def tell_date():
    try:
        now = datetime.datetime.now()
        current_date = now.strftime("%A, %B %d, %Y")
        response = f"Today's date is {current_date}."
        speak(response)
        return {"text": response}
    except Exception as e:
        error_msg = f"Error getting date: {str(e)}"
        speak(error_msg)
        return {"text": error_msg}

# Music library
music = {
    "stealth": "https://www.youtube.com/watch?v=U47Tr9BB_wE",
    "march": "https://www.youtube.com/watch?v=Xqeq4b5u_Xw",
    "skyfall": "https://www.youtube.com/watch?v=DeumyOzKqgI",
    "believer": "https://www.youtube.com/watch?v=7wtfhZwyrcc",
    "shape of you": "https://www.youtube.com/watch?v=JGwWNGJdvx8",
    "lecture": "https://www.youtube.com/watch?v=ZOhUXDe1Xr0&list=PL5Dqs90qDljVjbp18F1uw8cXgOobTOFGf"
}

def take_command():
    """Voice command recognition"""
    if not SPEECH_RECOGNITION_AVAILABLE:
        return {"text": "Voice recognition not available. Please use text commands."}
    
    try:
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            print("Listening...")
            recognizer.adjust_for_ambient_noise(source, duration=1)
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
            
        command = recognizer.recognize_google(audio)
        print(f"Voice Command: {command}")
        return command.lower()
    except sr.UnknownValueError:
        return "Sorry, I didn't catch that. Please repeat."
    except sr.RequestError as e:
        return f"Speech recognition error: {str(e)}"
    except sr.WaitTimeoutError:
        return "No speech detected"
    except Exception as e:
        return f"Voice error: {str(e)}"

def play_music(track_name):
    """Play music from YouTube"""
    try:
        track_name = track_name.lower().strip()
        if track_name in music:
            response = f"Opening {track_name} on YouTube..."
            speak(response)
            webbrowser.open(music[track_name])
            return {"text": response, "action": "music_played"}
        else:
            available = ", ".join(music.keys())
            response = f"Track not found. Available tracks: {available}"
            speak(response)
            return {"text": response}
    except Exception as e:
        error_msg = f"Error playing music: {str(e)}"
        speak(error_msg)
        return {"text": error_msg}

def google_search(query):
    """Perform Google search"""
    try:
        search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        webbrowser.open(search_url)
        response = f"Opening Google search for: {query}"
        speak(response)
        return {"text": response, "action": "web_opened"}
    except Exception as e:
        error_msg = f"Error opening search: {str(e)}"
        speak(error_msg)
        return {"text": error_msg}

def get_weather():
    """Get weather information"""
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
            speak(weather_report)
            return {"text": weather_report}
        else:
            error_message = data.get('message', 'Weather service unavailable')
            response = f"Weather error: {error_message}"
            speak(response)
            return {"text": response}
    except requests.exceptions.RequestException as e:
        error_msg = f"Network error getting weather: {str(e)}"
        speak(error_msg)
        return {"text": error_msg}
    except Exception as e:
        error_msg = f"Weather error: {str(e)}"
        speak(error_msg)
        return {"text": error_msg}

def get_article():
    """Get news articles"""
    try:
        webbrowser.open("https://news.google.com")
        response = "Opening Google News for latest articles."
        speak(response)
        return {"text": response, "action": "web_opened"}
    except Exception as e:
        error_msg = f"Error opening news: {str(e)}"
        speak(error_msg)
        return {"text": error_msg}

def battery_status():
    """Get battery status"""
    if not PSUTIL_AVAILABLE:
        response = "Battery monitoring not available on this system."
        speak(response)
        return {"text": response}
    
    try:
        battery = psutil.sensors_battery()
        if battery:
            percent = battery.percent
            charging = "charging" if battery.power_plugged else "not charging"
            response = f"Battery: {percent}% and {charging}."
            speak(response)
            return {"text": response}
        else:
            response = "Battery information not available."
            speak(response)
            return {"text": response}
    except Exception as e:
        error_msg = f"Battery error: {str(e)}"
        speak(error_msg)
        return {"text": error_msg}

def safe_calculate(expression):
    """Safely calculate mathematical expressions"""
    try:
        # Remove 'calculate' and 'what is' from expression
        expression = expression.replace('calculate', '').replace('what is', '').strip()
        
        # Only allow safe mathematical characters
        allowed_chars = set("0123456789+-*/.() ")
        if not expression or not all(c in allowed_chars for c in expression):
            return "Invalid mathematical expression"
        
        # Use eval with restricted scope for safety
        result = eval(expression, {"__builtins__": {}}, {})
        return str(result)
    except ZeroDivisionError:
        return "Error: Division by zero"
    except Exception as e:
        return f"Calculation error: {str(e)}"

def open_application(app_name):
    """Open system applications"""
    try:
        system = platform.system().lower()
        
        if app_name == "calculator":
            if system == "windows":
                subprocess.run(['calc'], check=True)
            elif system == "darwin":  # macOS
                subprocess.run(['open', '-a', 'Calculator'], check=True)
            else:  # Linux
                subprocess.run(['gnome-calculator'], check=True)
            return "Calculator opened successfully"
        else:
            return f"Application '{app_name}' not supported"
    except subprocess.CalledProcessError as e:
        return f"Error opening {app_name}: {str(e)}"
    except FileNotFoundError:
        return f"{app_name} not found on this system"
    except Exception as e:
        return f"Error: {str(e)}"

def take_screenshot():
    """Take a screenshot"""
    if not SCREENSHOT_AVAILABLE:
        response = "Screenshot functionality not available."
        speak(response)
        return {"text": response}
    
    try:
        response = "Taking screenshot..."
        speak(response)
        screenshot = pyautogui.screenshot()
        screenshot.save("screenshot.png")
        final_response = "Screenshot saved as screenshot.png"
        speak(final_response)
        return {"text": final_response, "action": "screenshot_taken"}
    except Exception as e:
        error_msg = f"Screenshot error: {str(e)}"
        speak(error_msg)
        return {"text": error_msg}

def take_picture():
    """Take a picture using webcam"""
    if not CAMERA_AVAILABLE:
        response = "Camera functionality not available."
        speak(response)
        return {"text": response}
    
    try:
        response = "Taking picture... Please smile!"
        speak(response)
        ecapture.capture(0, "ECHO Assistant", "captured_image.jpg")
        final_response = "Picture captured as captured_image.jpg"
        speak(final_response)
        return {"text": final_response, "action": "picture_taken"}
    except Exception as e:
        error_msg = f"Camera error: {str(e)}"
        speak(error_msg)
        return {"text": error_msg}

def get_joke():
    """Get a random joke"""
    if not JOKES_AVAILABLE:
        # Fallback jokes
        jokes = [
            "Why don't scientists trust atoms? Because they make up everything!",
            "Why did the computer go to the doctor? Because it had a virus!",
            "Why don't robots ever panic? Because they have nerves of steel!"
        ]
        import random
        joke = random.choice(jokes)
    else:
        try:
            joke = pyjokes.get_joke()
        except:
            joke = "Why don't scientists trust atoms? Because they make up everything!"
    
    speak(joke)
    return {"text": joke}

def process_mood(mood_input):
    """Process mood-related input"""
    mood_input = mood_input.lower()
    
    if any(word in mood_input for word in ['happy', 'good', 'great', 'fine', 'awesome', 'excellent', 'wonderful']):
        response = "That's wonderful to hear! Keep smiling! You're doing great and shining like a star today!"
    elif any(word in mood_input for word in ['sad', 'down', 'unhappy', 'depressed', 'low']):
        response = ("I'm sorry to hear that. Remember, after every storm comes a rainbow. "
                   "It's okay to have tough days, but they don't define you. "
                   "Every challenge is an opportunity to grow stronger. "
                   "Take a deep breath and know that brighter days are ahead. "
                   "I'm here if you need someone to listen.")
    elif any(word in mood_input for word in ['tired', 'exhausted', 'sleepy', 'drained']):
        response = "You should take some rest. A short break might help you recharge. You deserve it!"
    elif any(word in mood_input for word in ['angry', 'upset', 'frustrated', 'mad']):
        response = ("Try taking deep breaths and count to ten. It's okay to feel angry sometimes, "
                   "but it's important to find healthy ways to express those feelings. Everything will be okay.")
    elif any(word in mood_input for word in ['excited', 'energetic', 'enthusiastic', 'pumped']):
        response = "Awesome! Your energy is contagious! Keep that enthusiasm up!"
    else:
        response = "Thanks for sharing how you feel. I'm here whenever you want to talk."
    
    speak(response)
    return {"text": response}

def execute_command(command):
    """Main command execution function"""
    if not command or not command.strip():
        response = "Please provide a command."
        speak(response)
        return {"text": response}
    
    command = command.lower().strip()
    print(f"Processing command: {command}")
    
    try:
        # Time and Date
        if any(word in command for word in ['time', 'clock']):
            return tell_time()
        
        elif any(word in command for word in ['date', 'today']):
            return tell_date()
        
        # Greetings
        elif any(word in command for word in ['hello', 'hi', 'hey']):
            response = "Hello! I'm ECHO, your Enhanced Cognitive Holographic Operator. How can I assist you today?"
            speak(response)
            return {"text": response}
        
        # Music
        elif 'play' in command:
            track_name = command.replace('play', '').strip()
            return play_music(track_name)
        
        # Web Applications
        elif 'open google' in command:
            webbrowser.open("https://www.google.co.in/")
            response = "Opening Google fo you..."
            speak(response)
            return {"text": response, "action": "web_opened"}
        
        elif 'open youtube' in command:
            webbrowser.open("https://www.youtube.com/")
            response = "Opening YouTube..."
            speak(response)
            return {"text": response, "action": "web_opened"}
        
        elif 'open chatgpt' in command:
            webbrowser.open("https://chat.openai.com/")
            response = "Opening ChatGPT..."
            speak(response)
            return {"text": response, "action": "web_opened"}
        
        elif 'open whatsapp' in command:
            webbrowser.open("https://web.whatsapp.com/")
            response = "Opening WhatsApp Web..."
            speak(response)
            return {"text": response, "action": "web_opened"}
        
        # Calculator
        elif 'open calculator' in command:
            result = open_application("calculator")
            speak(result)
            return {"text": result}
        
        # Calculations
        elif any(phrase in command for phrase in ['calculate', 'what is', 'compute']) and any(char in command for char in '0123456789+-*/.'):
            result = safe_calculate(command)
            response = f"The result is: {result}"
            speak(response)
            return {"text": response}
        
        # Search
        elif 'search' in command:
            search_query = command.replace('search', '').strip()
            if search_query:
                return google_search(search_query)
            else:
                response = "Please specify what you want to search for."
                speak(response)
                return {"text": response}
        
        # Weather
        elif 'weather' in command:
            return get_weather()
        
        # Battery
        elif 'battery' in command:
            return battery_status()
        
        # Jokes
        elif any(word in command for word in ['joke', 'funny', 'humor']):
            return get_joke()
        
        # Screenshots and Pictures
        elif 'screenshot' in command:
            return take_screenshot()
        
        elif 'picture' in command or 'photo' in command:
            return take_picture()
        
        # News/Articles
        elif any(word in command for word in ['news', 'article']):
            return get_article()
        
        # Mood checking
        elif any(phrase in command for phrase in ['mood', 'how am i', 'how do i feel', 'feeling']):
            response = ("How are you feeling today? You can tell me if you're happy, sad, excited, "
                       "tired, or any other emotion you're experiencing.")
            speak(response)
            return {"text": response}
        
        # Mood responses
        elif any(word in command for word in ['happy', 'sad', 'angry', 'excited', 'tired', 'good', 'bad', 'great', 'awful']):
            return process_mood(command)
        
        # System commands
        elif any(word in command for word in ['exit', 'quit', 'goodbye', 'bye']):
            response = "Goodbye! ECHO signing off. Have a wonderful day!"
            speak(response)
            return {"text": response, "action": "exit"}
        
        # Help
        elif 'help' in command:
            response = ("I can help you with: time, date, calculations, web browsing, music, weather, "
                       "battery status, jokes, screenshots, mood checking, and much more. Just ask!")
            speak(response)
            return {"text": response}
        
        # Default response
        else:
            response = ("I understand you're trying to communicate with me. I can help with time, weather, "
                       "calculations, opening websites, playing music, and much more. What would you like to do?")
            speak(response)
            return {"text": response}
            
    except Exception as e:
        error_msg = f"An error occurred: {str(e)}"
        print(f"Error in execute_command: {error_msg}")
        speak(error_msg)
        return {"text": error_msg}

# Standalone mode for testing
if __name__ == "__main__":
    print("ECHO AI Assistant - Standalone Mode")
    speak("Hello Parth. How can I assist you today?")
    
    if SPEECH_RECOGNITION_AVAILABLE:
        print("Voice recognition available. Say 'exit' to quit.")
        while True:
            try:
                command = take_command()
                if isinstance(command, str) and command:
                    if 'exit' in command.lower():
                        break
                    result = execute_command(command)
                    print(f"Response: {result.get('text', 'No response')}")
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
    else:
        print("Voice recognition not available. Please use the web interface.")