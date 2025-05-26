"""Voice transcription service using OpenRouter's GPT-4o-mini"""
import os
from typing import Optional
import openrouter
import tempfile
import asyncio
from pathlib import Path

class TranscriptionService:
    def __init__(self, api_key: str):
        """Initialize the transcription service with OpenRouter API key"""
        self.client = openrouter.Client(api_key=api_key)
        self.model = "openai/gpt-4o-mini-2024-07-18"
    
    async def transcribe_voice(self, voice_bytes: bytes) -> Optional[str]:
        """
        Transcribe voice message bytes to text using OpenRouter's GPT-4o-mini
        
        Args:
            voice_bytes: Raw bytes of the voice message
            
        Returns:
            Transcribed text or None if transcription fails
        """
        try:
            # Save voice bytes to a temporary file
            with tempfile.NamedTemporaryFile(suffix='.ogg', delete=False) as temp_file:
                temp_file.write(voice_bytes)
                temp_file_path = temp_file.name
            
            try:
                # Convert OGG to WAV using ffmpeg (you'll need ffmpeg installed)
                wav_path = temp_file_path.replace('.ogg', '.wav')
                process = await asyncio.create_subprocess_exec(
                    'ffmpeg', '-i', temp_file_path, '-acodec', 'pcm_s16le', '-ar', '16000', wav_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await process.communicate()
                
                if not os.path.exists(wav_path):
                    print("Failed to convert voice file to WAV format")
                    return None
                
                # Read the WAV file
                with open(wav_path, 'rb') as wav_file:
                    audio_data = wav_file.read()
                
                # Call OpenRouter API for transcription
                response = await self.client.audio.transcriptions.create(
                    model=self.model,
                    file=audio_data,
                    file_name="voice_message.wav",
                    response_format="text"
                )
                
                return response.strip()
                
            finally:
                # Clean up temporary files
                try:
                    os.unlink(temp_file_path)
                    if os.path.exists(wav_path):
                        os.unlink(wav_path)
                except Exception as e:
                    print(f"Error cleaning up temporary files: {e}")
                    
        except Exception as e:
            print(f"Error in voice transcription: {e}")
            return None

# Create a singleton instance
transcription_service = None

def init_transcription_service(api_key: str):
    """Initialize the transcription service singleton"""
    global transcription_service
    transcription_service = TranscriptionService(api_key) 