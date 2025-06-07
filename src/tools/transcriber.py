import whisper
from langchain_core.tools import tool

@tool
def transcriber(audio_path: str, ai_model, use_gpu: bool = False) -> str:
    """
    Transcribes an audio file

    Parameters
    ----------
    audio_path : str
        Path to the audio file
    ai_model
        audio-to-text AI model. If None, a tiny-size Whisper model will be created
    use_gpu: bool
        Pass True if you are in a colab GPU environment or you have an integrated Nvidia GPU
    
    Returns:
        str: Text of the transcript 
    """
    
    if ai_model is None:
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