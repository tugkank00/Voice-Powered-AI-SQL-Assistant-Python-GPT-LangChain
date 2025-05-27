import logging
import openai
import os
from app.exceptions.domain import (
    VoiceTranscriptionException,
    OpenAIServiceException,
    ConfigurationException,
    InvalidFileFormatException
)
from app.services.base.protocols import VoiceToTextProtocol  

class OpenAIWhisperService(VoiceToTextProtocol):  
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            raise ConfigurationException("OPENAI_API_KEY")
        
        openai.api_key = api_key
    
    def transcribe(self, audio_file_path: str) -> str:
        self.logger.info(f"Transcribing audio file: {audio_file_path}")
        
        if not os.path.exists(audio_file_path):
            raise VoiceTranscriptionException(
                file_info={"file_path": audio_file_path, "error": "File not found"}
            )
        
        try:
            file_size = os.path.getsize(audio_file_path)
            if file_size == 0:
                raise VoiceTranscriptionException(
                    file_info={"file_path": audio_file_path, "file_size": file_size, "error": "Empty file"}
                )
            if file_size > 25 * 1024 * 1024:  
                raise VoiceTranscriptionException(
                    file_info={"file_path": audio_file_path, "file_size": file_size, "error": "File too large (>25MB)"}
                )
        except OSError as e:
            raise VoiceTranscriptionException(
                file_info={"file_path": audio_file_path, "error": f"Cannot access file: {e}"},
                original_exception=e
            )
        
        try:
            with open(audio_file_path, "rb") as audio_file:
                transcript = openai.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="text",
                    language="en"
                )
            
            if not transcript or transcript.strip() == "":
                raise VoiceTranscriptionException(
                    file_info={"file_path": audio_file_path, "file_size": file_size},
                    details={"reason": "No speech detected in audio"}
                )
            
            self.logger.info(f"Successfully transcribed: {len(transcript)} characters")
            return transcript.strip()
            
        except openai.APIError as e:
            self.logger.error(f"OpenAI Whisper API error: {e}")
            raise OpenAIServiceException(
                api_error=str(e),
                original_exception=e,
                details={
                    "service": "Whisper",
                    "file_size": file_size,
                    "file_path": audio_file_path
                }
            )
        except Exception as e:
            self.logger.error(f"Voice transcription error: {e}")
            raise VoiceTranscriptionException(
                file_info={"file_path": audio_file_path, "file_size": file_size},
                original_exception=e,
                details={"error_type": type(e).__name__}
            )