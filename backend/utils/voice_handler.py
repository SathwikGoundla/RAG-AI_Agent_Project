"""
Voice Handler Module
Handles speech-to-text and text-to-speech
"""

from typing import Optional, Tuple
import logging
import os

logger = logging.getLogger(__name__)


class VoiceHandler:
    """Handle voice input and output"""
    
    @staticmethod
    def speech_to_text(audio_file_path: str, language: str = "en-US") -> Tuple[str, float]:
        """
        Convert speech to text
        
        Args:
            audio_file_path: Path to audio file
            language: Language code (e.g., 'en-US', 'te-IN')
            
        Returns:
            Tuple of (recognized_text, confidence)
        """
        try:
            import speech_recognition as sr
            
            recognizer = sr.Recognizer()
            
            with sr.AudioFile(audio_file_path) as source:
                audio = recognizer.record(source)
            
            # Try Google Speech Recognition
            try:
                text = recognizer.recognize_google(audio, language=language)
                confidence = 0.9  # Google doesn't provide confidence
                logger.info(f"Speech recognized: {text[:50]}...")
                return text, confidence
            
            except sr.UnknownValueError:
                logger.warning("Could not understand audio")
                return "", 0.0
            except sr.RequestError as e:
                logger.error(f"Error with speech recognition service: {str(e)}")
                return "", 0.0
        
        except Exception as e:
            logger.error(f"Error in speech_to_text: {str(e)}")
            return "", 0.0
    
    @staticmethod
    def text_to_speech(text: str, language: str = "en", output_file: Optional[str] = None) -> Optional[str]:
        """
        Convert text to speech
        
        Args:
            text: Text to convert
            language: Language code ('en', 'te', etc.)
            output_file: Optional output file path
            
        Returns:
            Path to audio file or None
        """
        try:
            from gtts import gTTS
            
            # Create speech
            tts = gTTS(text=text, lang=language, slow=False)
            
            # Save to file
            if output_file is None:
                output_file = f"/tmp/speech_{id(text)}.mp3"
            
            os.makedirs(os.path.dirname(output_file) or ".", exist_ok=True)
            tts.save(output_file)
            
            logger.info(f"Text-to-speech saved to {output_file}")
            return output_file
        
        except Exception as e:
            logger.error(f"Error in text_to_speech: {str(e)}")
            return None
    
    @staticmethod
    def play_audio(audio_file_path: str) -> bool:
        """
        Play audio file
        
        Args:
            audio_file_path: Path to audio file
            
        Returns:
            True if successful
        """
        try:
            from pydub import AudioSegment
            from pydub.playback import play
            
            audio = AudioSegment.from_file(audio_file_path)
            play(audio)
            
            logger.info("Audio played successfully")
            return True
        
        except Exception as e:
            logger.error(f"Error playing audio: {str(e)}")
            return False
    
    @staticmethod
    def record_audio(duration: int = 10, output_file: Optional[str] = None) -> Optional[str]:
        """
        Record audio from microphone
        
        Args:
            duration: Recording duration in seconds
            output_file: Output file path
            
        Returns:
            Path to recorded audio file
        """
        try:
            import speech_recognition as sr
            from pydub import AudioSegment
            
            recognizer = sr.Recognizer()
            
            with sr.Microphone() as source:
                logger.info(f"Recording for {duration} seconds...")
                audio = recognizer.listen(source, timeout=duration)
            
            if output_file is None:
                output_file = f"/tmp/recording_{id(audio)}.wav"
            
            os.makedirs(os.path.dirname(output_file) or ".", exist_ok=True)
            
            # Save WAV file
            with open(output_file, "wb") as f:
                f.write(audio.get_wav_data())
            
            logger.info(f"Audio recorded and saved to {output_file}")
            return output_file
        
        except Exception as e:
            logger.error(f"Error recording audio: {str(e)}")
            return None
