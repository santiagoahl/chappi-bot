import whisper
from langchain_core.tools import tool

@tool
def transcriber(audio_path: str, use_gpu: bool = False) -> str:
    """
    Transcribes an audio file

    Parameters
    ----------
    audio_path : str or Path
        Path to an existing audio file (e.g., .wav, .mp3). Must be readable by ffmpeg.
    use_gpu: bool
        Pass True if you are in a colab GPU environment or you have an integrated Nvidia GPU
    
    Returns:
        str: Text of the transcript 
    """
    
    model_size = "tiny"
    ai_model = (
        whisper.load_model(model_size).cuda()
        if use_gpu
        else whisper.load_model(model_size)
    )
        
    raw_transcript = ai_model.transcribe(
        audio_path,
        word_timestamps=False,
        no_speech_threshold=0.5,
        condition_on_previous_text=True,
        compression_ratio_threshold=2.0,
    )
    
    transcript = raw_transcript["text"]
    
    return transcript

if __name__ == "__main__":
    audio_path = input("Pass your audio path to transcribe: ")
    print("Transcription:\n", "=" * 30, transcriber(audio_path))