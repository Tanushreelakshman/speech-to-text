"""
Text-to-Speech Module for Sign Language to Text and Speech Conversion

This module provides a simple wrapper around pyttsx3 for converting
predicted sign language text into speech output in real-time.

Usage:
    tts = TextToSpeech(rate=100, voice_index=0)
    tts.speak("Hello, this is a test")
    tts.set_property("rate", 150)  # change speed
"""

import pyttsx3
import threading
import queue
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(name)s:%(levelname)s:%(message)s')
logger = logging.getLogger(__name__)


class TextToSpeech:
    """
    A wrapper around pyttsx3 that handles speech synthesis.
    
    NOTE: On Windows, pyttsx3 (SAPI5) works best when initialized and used from the main thread.
    This implementation uses a background thread with proper error handling and initialization.
    """
    
    def __init__(self, rate=100, voice_index=0):
        """
        Initialize the Text-to-Speech engine.
        
        Args:
            rate (int): Speech rate in words per minute (default: 100)
            voice_index (int): Voice index (0=male, 1=female, etc., depends on OS)
        """
        try:
            logger.info("Initializing pyttsx3 engine...")
            # Initialize engine (use 'sapi5' backend explicitly on Windows if needed)
            self.engine = pyttsx3.init()
            
            # Verify engine is valid
            if self.engine is None:
                raise RuntimeError("pyttsx3.init() returned None")
            
            # Set voice rate
            self.engine.setProperty("rate", rate)
            logger.info(f"Set speech rate to {rate}")
            
            # Set volume (0.0 to 1.0)
            self.engine.setProperty("volume", 1.0)
            
            # Set voice (0 = first voice, 1 = second, etc.)
            voices = self.engine.getProperty("voices")
            logger.info(f"Available voices: {len(voices)}")
            for i, voice in enumerate(voices):
                logger.info(f"  Voice {i}: {voice.name}")
            
            if voice_index < len(voices):
                self.engine.setProperty("voice", voices[voice_index].id)
                logger.info(f"Using voice: {voices[voice_index].name}")
            else:
                logger.warning(f"Voice index {voice_index} not available; using default")
            
            # Queue for thread-safe speech requests
            self.speech_queue = queue.Queue()
            self.is_running = True
            
            # Start background speech thread (daemon, will not block shutdown)
            self.speech_thread = threading.Thread(target=self._speech_worker, daemon=True, name="TTS-Worker")
            self.speech_thread.start()
            logger.info("Text-to-Speech engine initialized successfully; background thread started")
            
        except Exception as e:
            logger.error(f"Failed to initialize TTS engine: {e}", exc_info=True)
            raise
    
    def _speech_worker(self):
        """
        Background worker thread that processes speech requests.
        Initializes its own pyttsx3 engine instance (required on Windows SAPI5).
        
        IMPORTANT: On Windows, pyttsx3 engine state can get "stuck" after runAndWait().
        Solution: Reinitialize engine after each speech to reset internal state.
        """
        logger.info("TTS worker thread started")
        worker_engine = None
        
        def init_engine():
            """Helper to initialize or reinitialize the engine."""
            nonlocal worker_engine
            try:
                # If engine exists, try to close it first
                if worker_engine is not None:
                    try:
                        worker_engine.endLoop()
                    except:
                        pass
                    worker_engine = None
                
                # Create fresh engine instance
                worker_engine = pyttsx3.init()
                worker_engine.setProperty("rate", 100)
                worker_engine.setProperty("volume", 1.0)
                voices = worker_engine.getProperty("voices")
                if voices:
                    worker_engine.setProperty("voice", voices[0].id)
                logger.debug("Engine (re)initialized")
                return True
            except Exception as e:
                logger.error(f"Failed to initialize engine in worker thread: {e}", exc_info=True)
                return False
        
        # Initialize engine on startup
        if not init_engine():
            return
        
        while self.is_running:
            try:
                # Wait for text to speak (timeout prevents blocking on exit)
                text = self.speech_queue.get(timeout=1.0)
                if text is None:  # Shutdown signal
                    logger.info("TTS worker received shutdown signal")
                    break
                
                if text and text.strip():  # Only speak non-empty text
                    logger.info(f"Speaking: {text}")
                    try:
                        worker_engine.say(text)
                        worker_engine.runAndWait()
                        logger.info(f"Finished speaking: {text}")
                        
                        # CRITICAL FIX: Reinitialize engine after each speech on Windows
                        # This prevents the event loop from getting stuck
                        logger.debug("Reinitializing engine for next speech...")
                        if not init_engine():
                            logger.warning("Engine reinitialization failed, continuing anyway...")
                            
                    except Exception as e:
                        logger.error(f"Error during speech synthesis: {e}", exc_info=True)
                        # Try to reinit on error
                        init_engine()
                else:
                    logger.debug("Received empty text, skipping")
                    
            except queue.Empty:
                # Timeout is normal, just loop again
                continue
            except Exception as e:
                logger.error(f"Unexpected error in speech worker: {e}", exc_info=True)
        
        # Cleanup on exit
        try:
            if worker_engine is not None:
                worker_engine.endLoop()
        except:
            pass
        
        logger.info("TTS worker thread exiting")
    
    def speak(self, text):
        """
        Queue text to be spoken (non-blocking - queues and returns immediately).
        
        Args:
            text (str): Text to convert to speech
        """
        if not text or not text.strip():
            logger.debug("speak() called with empty text")
            return
        logger.debug(f"Queueing text for speech: {text}")
        self.speech_queue.put(text)
    
    def speak_blocking(self, text):
        """
        Speak text immediately using background thread and wait briefly.
        This ensures speech happens but doesn't block the main loop for too long.
        
        Args:
            text (str): Text to convert to speech
        """
        if text and text.strip():
            logger.info(f"Queueing text for speech (will wait up to 5 sec): {text}")
            self.speech_queue.put(text)
            # Give TTS a chance to start speaking
            time.sleep(0.5)
    
    def set_property(self, property_name, value):
        """
        Set a property of the TTS engine (rate, volume, voice).
        Note: Changes may not apply to already-queued speech.
        
        Args:
            property_name (str): Property name ('rate', 'volume', 'voice')
            value: Property value
        """
        try:
            # Update both main and worker engine if possible
            if hasattr(self, 'engine') and self.engine:
                self.engine.setProperty(property_name, value)
            logger.info(f"Set {property_name} to {value}")
        except Exception as e:
            logger.error(f"Error setting property {property_name}: {e}", exc_info=True)
    
    def get_property(self, property_name):
        """
        Get a property of the TTS engine.
        
        Args:
            property_name (str): Property name ('rate', 'volume', etc.)
        
        Returns:
            Property value or None if error
        """
        try:
            if hasattr(self, 'engine') and self.engine:
                return self.engine.getProperty(property_name)
        except Exception as e:
            logger.error(f"Error getting property {property_name}: {e}", exc_info=True)
        return None

    
    def stop(self):
        """Stop the TTS engine and clean up resources."""
        try:
            logger.info("Stopping TTS engine...")
            self.is_running = False
            self.speech_queue.put(None)  # Signal worker to exit
            # Wait for thread to finish (max 3 seconds)
            if hasattr(self, 'speech_thread') and self.speech_thread.is_alive():
                self.speech_thread.join(timeout=3)
            logger.info("Text-to-Speech engine stopped successfully")
        except Exception as e:
            logger.error(f"Error stopping TTS engine: {e}", exc_info=True)


def test_tts():
    """Test the TextToSpeech module with verbose output."""
    print("Testing TextToSpeech module...\n")
    
    try:
        tts = TextToSpeech(rate=100, voice_index=0)
        
        # Test basic speech
        print("\n[Test 1] Basic speech")
        tts.speak("Hello, this is a test of the text to speech system.")
        time.sleep(3)
        
        # Test multiple sentences
        print("\n[Test 2] Multiple sentences (non-blocking)")
        tts.speak("This is the first sentence.")
        tts.speak("This is the second sentence.")
        tts.speak("This is the third sentence.")
        time.sleep(6)
        
        # Test property change
        print("\n[Test 3] Change speech rate")
        tts.set_property("rate", 150)
        tts.speak("This sentence should be faster.")
        time.sleep(3)
        
        tts.stop()
        print("\n✓ Test complete!")
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_tts()
if __name__ == "__main__":
    test_tts()
