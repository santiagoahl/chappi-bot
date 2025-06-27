import os, dotenv
from typing import Dict
from langchain.tools import tool
from tavily import TavilyClient
from pytubefix import YouTube
import subprocess

# Web search
from urllib.parse import quote_plus, urlparse, parse_qs, unquote
import requests
from bs4 import BeautifulSoup


dotenv.load_dotenv()

search_engine = TavilyClient(api_key=os.getenv(key="TAVILY_API_KEY"))

# TODO: integrate asyncronism
@tool
def web_search(query: str) -> str:  # Q: how to pass GuestState as type?
    """
    This tools searchs in the web to retrieve information related to the user query.

    Parameters
    ----------
    query : str
        Web search query

    Returns:
        str: Web search result

    Example:
        >>> search_tool.invoke(state={
            "gala_state": gala_state,
            "chat_history": {"user": "What is Uber"}
        })
        'The Uber you know, reimagined for business. Uber for Business is a platform for managing global rides and meals, and local deliveries, for companies of any size ...'
    """
    module_name = "Web Search Tool"
    # logging.info(f"[{module_name}] Running web search...")
    query = quote_plus(query)  # format query
    url = (
        f"https://html.duckduckgo.com/html/?q={query}"  # Process user query as http url
    )
    headers = {"User-Agent": "Mozilla/5.0"}

    http_query = {"url": url, "headers": headers}

    http_response = requests.get(**http_query)
    soup = BeautifulSoup(markup=http_response.text, features="html.parser")
    results_raw = soup.find_all(name="a", class_="result__a", limit=3)

    # logging.info(f"[{module_name}] Web search completed.")
    if not results_raw:
        return "No results found."

    formatted_results = []
    for i, tag in enumerate(results_raw, start=1):
        title = tag.get_text(strip=True)
        raw_href = tag.get("href", "")
        parsed = parse_qs(urlparse(raw_href).query)
        cleaned_url = (
            unquote(parsed.get("uddg", [""])[0]) if "uddg" in parsed else raw_href
        )
        formatted_results.append(f"{i}. [{title}]({cleaned_url})")

    return "\n\n".join(formatted_results)


@tool
def pull_youtube_video(
    url: str, output_dir: str, get_audio: bool = False, get_video: bool = False
) -> Dict:
    """
    Import Youtube video and audio to local.
    The output are one of two files: processed_yt_video.mp4 and yt_audio.mp3 saved in output_dir
    Use get_audio and get_video to indicate which file to pull from the youtube video URL (can be both)

    Parameters
    ----------
    url : str
        Youtube video URL

    get_audio: bool
        Pass True to retrieve the audio from the youtube URL

    get_video: bool
        Pass True to retrieve the video from the youtube URL

    Returns:
        Dict: Result message

    Example:
        >>> pull_youtube_video(
            url="https://www.youtube.com/watch?v=IMgN1MGRKgA",
            output_dir="data/temp/"
        )
        {"result": f"Data saved in 'data/temp/yt_audio.mp3' and '../../data/temp/processed_yt_video.mp4'"}
    """
    try:
        assert not ((get_audio == False) and (get_video == False))
    except AssertionError:
        raise AssertionError(
            "arguments get_audio, get_video cannot be both False. Please set one (or both) of them as True to run this module"
        )

    yt = YouTube(url)  # Youtube object that pulls video / audio
    output_message = "Data saved in: "

    # 1. Video Task
    if get_video:
        # Define filenames and paths to save imported video and audio files
        raw_yt_video_filename = "raw_yt_video.mp4"
        processed_yt_video_filename = "processed_yt_video.mp4"

        raw_yt_video_path = os.path.join(output_dir, raw_yt_video_filename)
        processed_yt_video_path = os.path.join(output_dir, processed_yt_video_filename)

        # Define how to import yt video: video file
        yt_video = (
            yt.streams.filter(only_video=True, fps=25, res="144p")
            .order_by("fps")
            .asc()
            .first()
        )

        # Download audio and raw video
        yt_video.download(output_path=output_dir, filename=raw_yt_video_filename)

        # Process the video to optimize memmory usage (create a new video file which is a version with fewer fps)
        new_fps = 1
        reduce_fps_cmd = f'ffmpeg -y -i {raw_yt_video_path} -filter:v "fps={new_fps}" -an {processed_yt_video_path}'
        subprocess.run(reduce_fps_cmd, shell=True)

        # Remove raw video
        remove_raw_video_cmd = f"rm {raw_yt_video_path}"
        subprocess.run(remove_raw_video_cmd, shell=True)
        output_message += f"{processed_yt_video_path} "

    # 2. Audio Task
    if get_audio:
        # Define filenames and paths to save audio files
        yt_audio_filename = "yt_audio.mp3"
        yt_audio_path = os.path.join(output_dir, yt_audio_filename)

        # Define how to import yt video: audio file
        yt = YouTube(url)
        yt_audio = yt.streams.filter(only_audio=True).first()

        # Download audio and raw video
        yt_audio.download(output_path=output_dir, filename=yt_audio_filename)
        output_message += f"{yt_audio_path}"

    return {"result": output_message}


def test_web_search():
    user_query = input("Pass a topic / word to search for: ")
    search_result = web_search.invoke(input=user_query, max_results=2)
    print("Results")
    print("=" * 40)
    print(search_result)


def test_yt_func():
    # fast unit testing
    yt_url = input("Pass YT url: ")
    output_dir = input("Pass output dir: ")
    result = pull_youtube_video.invoke(
        input={"url": yt_url, "output_dir": output_dir, "get_video": True}
    )
    print("result", result)


if __name__ == "__main__":
    test_web_search()
    # test_yt_func()

# TODO: chage module name to search.py
# TODO: pass Path in docstrings for better typing
