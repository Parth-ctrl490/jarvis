#!/usr/bin/env python3
"""
ECHO AI - Audio Dependencies Installation & Testing Script
Run this to fix all speech and voice recognition issues.
"""

import subprocess
import sys
import platform
import os

def run_command(command):
    """Run a system command and return success/failure"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def install_packages():
    """Install required Python packages"""
    print("Installing Python packages...")
    
    packages = [
        'pyttsx3',
        'SpeechRecognition', 
        'pyaudio',
        'requests',
        'psutil',
        'pyjokes',
        'flask'
    ]
    
    for package in packages:
        print(f"Installing {package}...")
        success, stdout, stderr = run_command(f"{sys.executable} -m pip install {package}")
        
        if success:
            print(f"✓ {package} installed successfully")
        else:
            print(f"✗ {package} failed: {stderr}")
            
            # Special handling for pyaudio
            if package == 'pyaudio':
                print("Trying alternative pyaudio installation...")
                
                # Try pipwin for Windows
                if platform.system().lower() == 'windows':
                    print("Installing pipwin...")
                    run_command(f"{sys.executable} -m pip install pipwin")
                    success, _, _ = run_command(f"{sys.executable} -m pipwin install pyaudio")
                    if success:
                        print("✓ pyaudio installed via pipwin")
                    else:
                        print("✗ pyaudio still failed. Manual installation may be required.")

def install_system_dependencies():
    """Install system-level audio dependencies"""
    system = platform.system().lower()
    
    if system == 'linux':
        print("Installing Linux audio dependencies...")
        commands = [
            'sudo apt-get update',
            'sudo apt-get install -y portaudio19-dev python3-pyaudio',
            'sudo apt-get install -y espeak espeak-data libespeak-dev',
            'sudo apt-get install -y pulseaudio alsa-utils'
        ]
        
        for cmd in commands:
            print(f"Running: {cmd}")
            success, _, stderr = run_command(cmd)
            if success:
                print("✓ Success")
            else:
                print(f"⚠ Warning: {stderr}")
    
    elif system == 'darwin':  # macOS
        print("Installing macOS audio dependencies...")
        # Check if brew is installed
        success, _, _ = run_command('which brew')
        if not success:
            print("Homebrew not found. Please install Homebrew first:")
            print("Visit: https://brew.sh/")
        else:
            commands = [
                'brew install portaudio',
                'brew install espeak'
            ]
            for cmd in commands:
                print(f"Running: {cmd}")
                run_command(cmd)

def test_audio_systems():
    """Test if audio systems are working"""
    print("\n" + "="*50)
    print("TESTING AUDIO SYSTEMS")
    print("="*50)
    
    # Test TTS
    print("\n1. Testing Text-to-Speech...")
    try:
        import pyttsx3
        engine = pyttsx3.init()
        print("✓ pyttsx3 imported successfully")
        
        engine.say("Text to speech test successful")
        engine.runAndWait()
        print("✓ TTS test completed")
        
    except ImportError:
        print("✗ pyttsx3 not available")
    except Exception as e:
        print(f"✗ TTS error: {e}")
    
    # Test Speech Recognition
    print("\n2. Testing Speech Recognition...")
    try:
        import speech_recognition as sr
        print("✓ SpeechRecognition imported")
        
        import pyaudio
        print("✓ PyAudio imported")
        
        r = sr.Recognizer()
        mics = sr.Microphone.list_microphone_names()
        print(f"✓ Found {len(mics)} microphone(s)")
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
    except Exception as e:
        print(f"✗ Microphone error: {e}")
    
    # Test other dependencies
    print("\n3. Testing other dependencies...")
    modules = ['requests', 'psutil', 'pyjokes', 'flask']
    
    for module in modules:
        try:
            __import__(module)
            print(f"✓ {module} available")
        except ImportError:
            print(f"✗ {module} missing")

def main():
    """Main installation and testing function"""
    print("ECHO AI - Audio System Installation & Diagnostics")
    print("="*60)
    print(f"Python: {sys.version}")
    print(f"Platform: {platform.system()} {platform.release()}")
    print("="*60)
    
    # Install system dependencies first
    install_system_dependencies()
    
    # Install Python packages
    install_packages()
    
    # Test everything
    test_audio_systems()
    
    print("\n" + "="*60)
    print("INSTALLATION COMPLETE!")
    print("="*60)
    print("Now you can run:")
    print("1. python main.py  (for standalone mode)")
    print("2. python app.py   (for web interface)")
    print("="*60)

if __name__ == "__main__":
    main()