from langchain.tools import tool
from ultralytics import YOLO
import subprocess


@tool
def detect_objects(
    video_path: str, remove_after: bool = True, yolo_model: str = "yolov8s.pt"
) -> dict:
    """
    Object detection task for a given video file (e.g. .mp4 file).

    Parameters
    ----------
    video_path: str
        Path to the video file (e.g. .mp4 file)

    remove_after: bool
        Pass True if it is desired to remove after finishing task, which is optimal for memory-usage reasons-

    yolo_model: str
        Path or name of the model to use. For, custom tasks such as bird species detection, pass 'external/ai-models/bird-species-detection.pt' as arg value

    Returns:
        dict: Dict containing keys "video_path" (The same as input) and "detected_object" (A list of dicts, each dict has keys "frame" -the ith frame- and "result" -a list of detected objects in the ith frame-)

    Example:
        >>> detect_objects(video_path='../../data/temp/processed_yt_video.mp4')
        '{
            "video_path": video_path,
            "detected_objects":  [
                {'frame': 1, 'result': []},
                {'frame': 2, 'result':
                    [
                        'person',
                        'bird',
                        'bird'
                    ]},
                ...
                {'frame': 121, 'result': []}
                ]
        }'
    """

    def summarize(results):
        # Module to retrieve data on stream
        for i, result in enumerate(results):
            yield {
                "frame": i + 1,
                "result": [result.names[int(cls)] for cls in result.boxes.cls],
            }

    cv_model = YOLO(
        model=yolo_model, task="detect"
    )  # Initialize object detection model
    cv_results_raw = cv_model.predict(
        source=video_path, stream=True
    )  # Identify video objects
    cv_results_processed = list(
        summarize(cv_results_raw)
    )  # Process / clean model results

    if remove_after:
        # Remove raw video
        remove_processed_video_cmd = (
            f"rm {video_path}"  # Warning: take caution when modifying this line
        )
        subprocess.run(remove_processed_video_cmd, shell=True)

    # Prepare tool results
    processed_data = {
        "video_path": video_path,
        "detected_objects": cv_results_processed,
    }

    return processed_data


def test_detect_objects():
    print("Testing Object Detection Task...")
    objects = detect_objects.invoke(
        input={
            "video_path": "data/temp/processed_yt_video.mp4",
            "remove_after": False,
            "yolo_model": "external/ai-models/best.pt"
        }
    )
    print("\n")
    print("=" * 30)
    print("\nResults: \n")
    print(objects)


if __name__ == "__main__":
    test_detect_objects()


# TODO: make this a typed dict to let the agent better process this data
# TODO: Delete unnecesary videos
# TODO: Change folder name: tools_poc/ -> tools-poc/
