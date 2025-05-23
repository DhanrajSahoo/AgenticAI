from crewai.tools import BaseTool
from pydantic import BaseModel, Field
import sounddevice as sd
import soundfile as sf
from pydub import AudioSegment
from datetime import datetime
from typing import Type
import os

class VoiceRecordSchema(BaseModel):
    duration: int = Field(..., description="Duration of recording in seconds")
    
class VoiceRecorderTool(BaseTool):
    name: str = "Voice Recorder Tool"
    description: str = "Records audio from the microphone and saves it as an MP3 file"
    args_schema: str = VoiceRecordSchema

    def _run(self, duration=30) -> str:
        # Create absolute path for workspace/audio directory
        os.makedirs("workspace/audio", exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        wav_file = f"workspace/audio/recording_{timestamp}.wav" 
        #mp3_file = f"workspace/audio/recording_{timestamp}.mp3"

        try:
            samplerate = 44100
            message = f"🎙️ Recording started for {duration} seconds...\n"
            print(f"🎙️ Recording started for {duration} seconds...\n")
            audio = sd.rec(int(samplerate * duration), samplerate=samplerate, channels=1)
            sd.wait()
            
            sf.write(wav_file, audio, samplerate)
            print(f"[INFO] WAV saved to {wav_file}")

            # Convert WAV to MP3
            #sound = AudioSegment.from_wav(wav_file)
            #sound.export(mp3_file, format="mp3")
            #print(f"[INFO] MP3 saved to {mp3_file}")
            

            # Optionally, delete the WAV file
            #os.remove(wav_file)

            return os.path.abspath(wav_file)
        except FileNotFoundError as e:  
            return f"❌ File not found: {str(e)}"
        except Exception as e:
            return f"❌ Recording failed: {str(e)}"
        
    #def run(self, input_data: VoiceRecordSchema) -> str:
    def run(self) -> str:
        return self._run()