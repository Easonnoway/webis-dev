from typing import Any, Dict, List, Optional
import os
import cv2
from webis.core.pipeline import PipelineContext
from webis.core.plugin import Plugin

class VideoKeyframeExtractorPlugin(Plugin):
    """
    Plugin to extract keyframes from a video file.
    """
    def __init__(self, interval_seconds: int = 2, output_dir: str = "extracted_frames"):
        self.interval_seconds = interval_seconds
        self.output_dir = output_dir

    def initialize(self, context: PipelineContext):
        pass

    def run(self, context: PipelineContext, **kwargs) -> Dict[str, Any]:
        video_path = kwargs.get("video_path") or context.get("video_path")
        if not video_path:
            raise ValueError("video_path is required")
        
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")

        # Create output directory if it doesn't exist
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise RuntimeError(f"Could not open video file: {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps == 0:
             # Fallback if FPS cannot be determined
             fps = 30
             
        frame_interval = int(fps * self.interval_seconds)
        if frame_interval == 0:
            frame_interval = 1
        
        extracted_frames = []
        frame_count = 0
        saved_count = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_count % frame_interval == 0:
                # Use a safe filename
                base_name = os.path.basename(video_path)
                frame_filename = f"frame_{saved_count}_{base_name}.jpg"
                frame_path = os.path.join(self.output_dir, frame_filename)
                cv2.imwrite(frame_path, frame)
                extracted_frames.append(frame_path)
                saved_count += 1

            frame_count += 1

        cap.release()

        result = {
            "video_path": video_path,
            "extracted_frames": extracted_frames
        }
        
        context.set("extracted_frames", extracted_frames)
        
        return result
