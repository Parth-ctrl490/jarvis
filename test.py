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
import base64

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

# ==================== AI IMAGE GENERATION ====================
def generate_image(prompt):
    """
    Generate an image using Pollinations AI (FREE, no API key needed)
    Alternative: Can also use Stable Diffusion API or other services
    """
    try:
        print(f"Generating image for prompt: {prompt}")
        
        # Create captures directory if it doesn't exist
        os.makedirs("captures", exist_ok=True)
        
        # Clean the prompt for URL
        clean_prompt = prompt.strip()
        
        # Using Pollinations AI - FREE image generation
        # Encode prompt for URL
        encoded_prompt = requests.utils.quote(clean_prompt)
        image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true"
        
        # Download the image
        response = requests.get(image_url, timeout=30)
        
        if response.status_code == 200:
            # Save the image
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"generated_{timestamp}.png"
            filepath = os.path.join("captures", filename)
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            return {
                "text": f"Image generated successfully! Prompt: '{prompt}'",
                "action": "image_generated",
                "image_url": f"/captures/{filename}",
                "filename": filename
            }
        else:
            return {"text": "Failed to generate image. Please try again with a different prompt."}
            
    except Exception as e:
        error_msg = f"Image generation error: {str(e)}"
        print(error_msg)
        return {"text": "Sorry, I couldn't generate the image. Please try again."}

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
    'send whatsapp', 'whatsapp send', 'send message',
        'play music', 'play ',
        'screenshot', 'take picture', 'photo',
        'generate image', 'create image', 'draw', 'make image',
        'time', 'date',
        'weather',
        'battery',
        'news', 'article',
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
        'help','add contact', 'remove contact', 'list contacts', 'search contact',
    'send whatsapp', 'whatsapp send', 'send message', 'message',
        'exit', 'quit', 'goodbye', 'bye'
    ]
    
    for keyword in system_keywords:
        if keyword in command_lower:
            return True, keyword
    
    return False, None

# ==================== ADVANCED FEATURES ====================

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
CONTACTS_FILE = "echo_contacts.json"


def load_contacts():
    """Load contacts from file (name -> phone number)"""
    if os.path.exists(CONTACTS_FILE):
        try:
            with open(CONTACTS_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_contacts(contacts):
    try:
        with open(CONTACTS_FILE, 'w') as f:
            json.dump(contacts, f, indent=2)
    except Exception as e:
        print(f"Error saving contacts: {e}")



def list_contacts():
    try:
        contacts = load_contacts()
        if not contacts:
            return {"text": "No contacts saved yet."}
        resp = "Saved contacts:\n"
        for i, (name, phone) in enumerate(contacts.items(), start=1):
            resp += f"{i}. {name} -> {phone}\n"
        return {"text": resp}
    except Exception as e:
        return {"text": f"Error listing contacts: {str(e)}"}


def remove_contact(command):
    try:
        match = re.search(r'remove contact\s+(.+)', command, re.IGNORECASE)
        if not match:
            return {"text": "Usage: remove contact <Name>"}
        name = match.group(1).strip()
        contacts = load_contacts()
        if name in contacts:
            phone = contacts.pop(name)
            save_contacts(contacts)
            return {"text": f"Removed contact {name} -> {phone}"}
        else:
            return {"text": f"Contact '{name}' not found."}
    except Exception as e:
        return {"text": f"Error removing contact: {str(e)}"}

def send_whatsapp(command):
    """
    Enhanced WhatsApp message sending with multiple command formats support.
    
    Supported formats:
    - send whatsapp to <Name> : <message>
    - whatsapp <Name> : <message>
    - message <Name> on whatsapp : <message>
    - send <Name> <message> (auto-detects WhatsApp context)
    """
    try:
        command_lower = command.lower()
        
        # Load contacts
        contacts = load_contacts()
        
        # Pattern 1: Explicit colon separator (most reliable)
        # Examples: "send whatsapp to John : Hello", "message Mom : How are you"
        if ':' in command:
            parts = command.split(':', 1)
            if len(parts) == 2:
                target_part = parts[0].strip()
                message = parts[1].strip()
                
                # Extract target name/number from first part
                # Remove command keywords
                for keyword in ['send whatsapp to', 'whatsapp send to', 'message', 'send to', 'whatsapp', 'send']:
                    target_part = re.sub(rf'\b{keyword}\b', '', target_part, flags=re.IGNORECASE).strip()
                
                target = target_part
        
        # Pattern 2: No colon - try to intelligently parse
        else:
            # Remove WhatsApp-related keywords to extract core command
            clean_cmd = command
            for keyword in ['send whatsapp to', 'whatsapp send to', 'send message to', 'message', 'send to', 'whatsapp', 'send']:
                clean_cmd = re.sub(rf'\b{keyword}\b', '', clean_cmd, flags=re.IGNORECASE).strip()
            
            # Try to find contact name first (exact match in contacts list)
            target = None
            message = None
            
            # Check if any contact name appears in the command
            for contact_name in contacts.keys():
                # Case-insensitive search for contact name
                pattern = rf'\b{re.escape(contact_name)}\b'
                match = re.search(pattern, clean_cmd, re.IGNORECASE)
                if match:
                    target = contact_name
                    # Everything after the contact name is the message
                    start_pos = match.end()
                    message = clean_cmd[start_pos:].strip()
                    break
            
            # If no contact found, try phone number pattern
            if not target:
                # Look for phone number pattern
                phone_match = re.search(r'(\+?\d{10,15})', clean_cmd)
                if phone_match:
                    target = phone_match.group(1)
                    # Message is everything after the phone number
                    message = clean_cmd[phone_match.end():].strip()
                else:
                    # Fallback: assume first word(s) are target, rest is message
                    # Split on first 2-3 words as potential target
                    words = clean_cmd.split()
                    if len(words) >= 2:
                        # Try 2-word names first (e.g., "John Doe")
                        potential_target = ' '.join(words[:2])
                        if potential_target.title() in contacts or potential_target in contacts:
                            target = potential_target
                            message = ' '.join(words[2:])
                        else:
                            # Try single word
                            target = words[0]
                            message = ' '.join(words[1:])
                    else:
                        return {"text": "Usage: send whatsapp to <Name or Phone> : <message>"}
        
        # Validate we have both target and message
        if not target or not message:
            return {
                "text": "Please provide both contact/number and message. Examples:\n"
                        "• send whatsapp to John : Hello there\n"
                        "• whatsapp Mom : On my way home\n"
                        "• message +919876543210 : Meeting at 5pm"
            }
        
        # Resolve phone number
        phone = None
        contact_name = target  # Store for response message
        
        # Check if target is a saved contact name (case-insensitive)
        for name, number in contacts.items():
            if name.lower() == target.lower():
                phone = number
                contact_name = name  # Use the correctly-cased name
                break
        
        # If not found in contacts, check if it's a valid phone number
        if not phone:
            # Clean and validate phone number
            cleaned_number = re.sub(r'[^\d+]', '', target)
            if re.match(r'^\+?\d{10,15}$', cleaned_number):
                phone = cleaned_number
                contact_name = cleaned_number  # Use number as display name
            else:
                # Fuzzy match attempt for contact names
                possible_matches = [name for name in contacts.keys() 
                                  if target.lower() in name.lower()]
                
                if len(possible_matches) == 1:
                    # Found one fuzzy match
                    contact_name = possible_matches[0]
                    phone = contacts[contact_name]
                    return {
                        "text": f"Did you mean '{contact_name}'? Sending message...",
                        "action": "whatsapp_confirm"
                    }
                elif len(possible_matches) > 1:
                    # Multiple matches found
                    matches_str = ", ".join(possible_matches)
                    return {
                        "text": f"Multiple contacts found: {matches_str}. Please be more specific."
                    }
                else:
                    # No matches found
                    return {
                        "text": f"Contact '{target}' not found. Add contact first with:\n"
                                f"add contact {target} : +91XXXXXXXXXX\n"
                                f"Or use the phone number directly."
                    }
        
        # Format phone for WhatsApp (remove all non-digits except leading +)
        phone_digits = re.sub(r'[^\d]', '', phone)
        
        # Ensure country code is present
        if not phone.startswith('+') and len(phone_digits) == 10:
            # Assume Indian number if 10 digits
            phone_digits = '91' + phone_digits
        
        # URL encode the message
        encoded_message = requests.utils.quote(message)
        
        # Create WhatsApp URLs
        # Protocol URL (for WhatsApp Desktop app)
        protocol_url = f"whatsapp://send?phone={phone_digits}&text={encoded_message}"
        
        # Web URL (fallback)
        web_url = f"https://web.whatsapp.com/send?phone={phone_digits}&text={encoded_message}"
        
        # Try to open WhatsApp
        opened_urls = {}
        
        # Try desktop app first
        try:
            webbrowser.open(protocol_url)
            opened_urls['desktop'] = protocol_url
        except Exception as e:
            print(f"Desktop app open failed: {e}")
    
        
        # Auto-send functionality (if pyautogui available)
        auto_send_status = None
        if SCREENSHOT_AVAILABLE:  # Using SCREENSHOT_AVAILABLE as proxy for pyautogui
            try:
                import time
                import pyautogui
                
                # Wait for WhatsApp to load
                time.sleep(5)
                
                # Press Enter to send
                pyautogui.press('enter')
                auto_send_status = "success"
                
            except Exception as e:
                auto_send_status = f"failed: {str(e)}"
                print(f"Auto-send error: {e}")
        
        # Prepare response
        response_text = f"✅ Opening WhatsApp for {contact_name}...\n"
        response_text += f"📱 Message: \"{message}\"\n"
        
        if auto_send_status == "success":
            response_text += "✉️ Message sent automatically!"
        else:
            response_text += "👉 Please press Enter in WhatsApp to send."
        
        return {
            "text": response_text,
            "action": "whatsapp_sent",
            "contact": contact_name,
            "phone": phone_digits,
            "message": message,
            "opened_urls": opened_urls,
            "auto_send": auto_send_status
        }
        
    except Exception as e:
        error_msg = f"WhatsApp error: {str(e)}"
        print(error_msg)
        return {
            "text": "❌ Failed to send WhatsApp message. Please try again or check your internet connection.",
            "error": str(e)
        }


# Enhanced contact management functions

def add_contact(command):
    """
    Add a contact with flexible input formats.
    
    Supported formats:
    - add contact John +919876543210
    - add contact John : +919876543210
    - add contact John Doe +919876543210
    """
    try:
        # Remove 'add contact' prefix
        clean_cmd = re.sub(r'\badd contact\b', '', command, flags=re.IGNORECASE).strip()
        
        # Split by colon if present
        if ':' in clean_cmd:
            parts = clean_cmd.split(':', 1)
            name = parts[0].strip()
            phone = parts[1].strip()
        else:
            # Find phone number pattern
            phone_match = re.search(r'(\+?\d{10,15})$', clean_cmd)
            if phone_match:
                phone = phone_match.group(1)
                name = clean_cmd[:phone_match.start()].strip()
            else:
                return {
                    "text": "Usage: add contact <Name> <phone>\n"
                            "Example: add contact Mom +919876543210"
                }
        
        # Validate phone number
        phone = re.sub(r'[^\d+]', '', phone)
        if not re.match(r'^\+?\d{10,15}$', phone):
            return {"text": "Invalid phone number. Format: +91XXXXXXXXXX (10-15 digits)"}
        
        # Add country code if missing
        if not phone.startswith('+'):
            if len(phone) == 10:
                phone = '+91' + phone  # Default to India
            else:
                phone = '+' + phone
        
        # Save contact
        contacts = load_contacts()
        
        # Check for duplicates
        if name in contacts:
            return {
                "text": f"⚠️ Contact '{name}' already exists with number {contacts[name]}.\n"
                        f"Use 'remove contact {name}' first to update."
            }
        
        contacts[name] = phone
        save_contacts(contacts)
        
        return {
            "text": f"✅ Contact saved successfully!\n"
                    f"📇 {name} → {phone}",
            "action": "contact_added",
            "contact": {"name": name, "phone": phone}
        }
        
    except Exception as e:
        return {"text": f"Error adding contact: {str(e)}"}


def search_contact(query):
    """Search for contacts by partial name match"""
    try:
        contacts = load_contacts()
        query_lower = query.lower()
        
        matches = {name: phone for name, phone in contacts.items() 
                  if query_lower in name.lower()}
        
        if not matches:
            return {"text": f"No contacts found matching '{query}'."}
        
        response = f"Found {len(matches)} contact(s):\n"
        for name, phone in matches.items():
            response += f"📇 {name} → {phone}\n"
        
        return {"text": response, "matches": matches}
        
    except Exception as e:
        return {"text": f"Error searching contacts: {str(e)}"}

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
    "lecture": "https://www.youtube.com/watch?v=ZOhUXDe1Xr0&list=PL5Dqs90qDljVjbp18F1uw8cXgOobTOFGf",
    "faded": "https://www.youtube.com/watch?v=60ItHLz5sQw",
    
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
            
            # Image Generation - NEW FEATURE
            if any(phrase in command_lower for phrase in ['generate image', 'create image', 'draw me', 'make image', 'generate picture']):
                # Extract the prompt
                prompt = command_lower
                for phrase in ['generate image of', 'create image of', 'draw me', 'make image of', 'generate picture of', 'generate image', 'create image', 'draw', 'make image']:
                    prompt = prompt.replace(phrase, '').strip()
                
                if not prompt:
                    return {"text": "Please provide a description for the image you want to generate."}
                
                return generate_image(prompt)
            
            # News and Articles - FIXED
            elif any(word in command_lower for word in ['news', 'article', 'headlines']):
                return get_article()
            
            # Time and Date
            elif any(word in command_lower for word in ['time', 'clock']):
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

            # Contacts management
            elif command_lower.startswith('add contact'):
                return add_contact(command)

            elif 'list contacts' in command_lower:
                return list_contacts()

            elif command_lower.startswith('remove contact'):
                return remove_contact(command)

            # WhatsApp sending
            elif any(phrase in command_lower for phrase in ['send whatsapp', 'whatsapp send', 'send message', 'whatsapp message', 'message on whatsapp']):
                return send_whatsapp(command)
            

            elif 'search contact' in command_lower:
                query = command.replace('search contact', '').strip()
                if query:
                    return search_contact(query)
                else:
                    return {"text": "Usage: search contact <name>"}
            
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
                    "🎨 AI IMAGE GENERATION (NEW!):\n"
                    "- 'generate image of [description]'\n"
                    "- 'create image of a sunset over mountains'\n"
                    "- 'draw me a futuristic city'\n\n"
                    "🛠️ SYSTEM COMMANDS:\n"
                    "⏰ Time & Date: 'time', 'date'\n"
                    "🎵 Music: 'play [song name]'\n"
                    "🌐 Web: 'open google/youtube/github/spotify/gmail'\n"
                    "🔍 Search: 'search [query]'\n"
                    "📰 News: 'news', 'article', 'headlines'\n"
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
    print("Now with conversational AI and image generation! Ask me anything or use system commands.")
    speak("Hello! I'm ECHO with enhanced conversational abilities and AI image generation. How can I assist you today?")
    
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
