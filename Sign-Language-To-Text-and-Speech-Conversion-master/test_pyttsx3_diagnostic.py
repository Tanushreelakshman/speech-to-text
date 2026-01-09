"""
Diagnostic script to test pyttsx3 on this Windows system.
Run this to verify TTS is working correctly.
"""

import sys
import pyttsx3
import time

print("=" * 60)
print("pyttsx3 Diagnostic Test")
print("=" * 60)

print(f"\nPython: {sys.version}")
print(f"pyttsx3 location: {pyttsx3.__file__}")

# Test 1: Basic initialization
print("\n[Test 1] Initialize pyttsx3...")
try:
    engine = pyttsx3.init()
    print("✓ Engine initialized")
except Exception as e:
    print(f"✗ Failed to initialize: {e}")
    sys.exit(1)

# Test 2: Get available voices
print("\n[Test 2] List available voices...")
try:
    voices = engine.getProperty("voices")
    print(f"✓ Found {len(voices)} voice(s):")
    for i, voice in enumerate(voices):
        print(f"  {i}: {voice.name} ({voice.id})")
except Exception as e:
    print(f"✗ Failed to get voices: {e}")

# Test 3: Set properties
print("\n[Test 3] Set speech properties...")
try:
    engine.setProperty("rate", 100)
    engine.setProperty("volume", 1.0)
    print("✓ Properties set (rate=100, volume=1.0)")
except Exception as e:
    print(f"✗ Failed to set properties: {e}")

# Test 4: Speak and wait
print("\n[Test 4] Speak a simple sentence...")
print(">>> Saying: 'Hello, this is a text to speech test.'")
try:
    engine.say("Hello, this is a text to speech test.")
    print("   (Waiting for speech to complete...)")
    engine.runAndWait()
    print("✓ Speech completed successfully")
except Exception as e:
    print(f"✗ Speech failed: {e}")

# Test 5: Test multiple sentences
print("\n[Test 5] Speak multiple sentences...")
sentences = [
    "The first sentence.",
    "The second sentence.",
    "The third sentence."
]

for i, text in enumerate(sentences, 1):
    try:
        print(f"   [{i}] {text}")
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print(f"   ✗ Failed: {e}")

print("\n[Test 6] Change rate and speak...")
try:
    engine.setProperty("rate", 150)
    print("   Rate set to 150 (faster)")
    engine.say("This should be faster.")
    engine.runAndWait()
    print("✓ Faster speech completed")
except Exception as e:
    print(f"✗ Failed: {e}")

print("\n" + "=" * 60)
print("Diagnostic complete!")
print("=" * 60)
print("\nIf you did NOT hear any audio:")
print("  1. Check your system volume")
print("  2. Check if speakers are connected")
print("  3. Try: pyttsx3 may need SAPI5 voices installed (Windows)")
print("  4. Or: Try installing espeak (Linux/Mac alternative)")
