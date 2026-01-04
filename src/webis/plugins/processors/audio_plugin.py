from typing import Any, Dict, Optional
import os
from webis.core.pipeline import PipelineContext
from webis.core.plugin import Plugin
from openai import OpenAI

class AudioTranscriberPlugin(Plugin):
    """
    Plugin to transcribe audio using OpenAI's Whisper API.
    """
    def __init__(self, api_key: Optional[str] = None, model: str = "whisper-1"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.client = None

    def initialize(self, context: PipelineContext):
        if not self.api_key:
            # Try to get from context config if not in env
            self.api_key = context.config.get("openai_api_key")
        
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)

    def run(self, context: PipelineContext, **kwargs) -> Dict[str, Any]:
        audio_path = kwargs.get("audio_path") or context.get("audio_path")
        if not audio_path:
            raise ValueError("audio_path is required")

        if not self.client:
             if not self.api_key:
                 self.api_key = os.getenv("OPENAI_API_KEY")
             if self.api_key:
                 self.client = OpenAI(api_key=self.api_key)
             else:
                 raise ValueError("OpenAI API key is required for AudioTranscriberPlugin")

        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        try:
            with open(audio_path, "rb") as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model=self.model,
                    file=audio_file
                )
            
            result = {
                "text": transcript.text,
                "audio_path": audio_path
            }
            
            # Store in context
            context.set("transcription", transcript.text)
            
            return result
        except Exception as e:
            raise RuntimeError(f"Audio transcription failed: {str(e)}")
