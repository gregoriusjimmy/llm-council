import speech_recognition as sr
import edge_tts
import asyncio
import pygame
import os
import tempfile
import whisper
import torch

class VoiceHandler:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        pygame.mixer.init()
        
        # Check for GPU
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Loading Whisper model on {self.device}...")
        try:
            # Load base model - good balance of speed/accuracy
            self.whisper_model = whisper.load_model("base", device=self.device)
            self.use_local_whisper = True
            print("Local Whisper model loaded.")
        except Exception as e:
            print(f"Failed to load Whisper: {e}. Falling back to Google API.")
            self.use_local_whisper = False

    def listen(self):
        """Listens to the microphone and returns the recognized text."""
        with sr.Microphone() as source:
            print("Listening...")
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            try:
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=15)
                print("Processing audio...")
                
                if self.use_local_whisper:
                    # Save audio to temp file for Whisper
                    try:
                        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                            tmp_file.write(audio.get_wav_data())
                            tmp_path = tmp_file.name
                        
                        # Transcribe
                        result = self.whisper_model.transcribe(tmp_path)
                        text = result["text"].strip()
                        
                        # Cleanup
                        os.remove(tmp_path)
                        return text
                    except Exception as e:
                        print(f"Whisper error: {e}")
                        return None
                else:
                    # Fallback to Google
                    text = self.recognizer.recognize_google(audio)
                    return text
                    
            except sr.WaitTimeoutError:
                return None
            except sr.UnknownValueError:
                return None
            except Exception as e:
                print(f"Audio error: {e}")
                return None

    async def _generate_audio(self, text, voice="en-US-ChristopherNeural"):
        """Generates audio file from text using Edge TTS."""
        communicate = edge_tts.Communicate(text, voice)
        # Create a temporary file
        fd, path = tempfile.mkstemp(suffix=".mp3")
        os.close(fd)
        await communicate.save(path)
        return path

    def speak(self, text, voice="en-US-ChristopherNeural"):
        """Synchronous wrapper to speak text."""
        try:
            # Run the async generation
            audio_path = asyncio.run(self._generate_audio(text, voice))
            
            # Play the audio
            pygame.mixer.music.load(audio_path)
            pygame.mixer.music.play()
            
            # Wait for playback to finish
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
                
            # Cleanup
            # We verify music is unloaded before removing
            pygame.mixer.music.unload()
            os.remove(audio_path)
        except Exception as e:
            print(f"Error in speech synthesis: {e}")

if __name__ == "__main__":
    # Test
    vh = VoiceHandler()
    print("Speak now:")
    text = vh.listen()
    if text:
        print(f"You said: {text}")
        vh.speak(f"You said: {text}")
