import ffmpeg
import os
import uuid
import logging

logger = logging.getLogger(__name__)

def merge_videos(video_paths, output_dir):
    """
    Merges multiple video files into a single video file using FFmpeg.
    """
    if not video_paths:
        raise ValueError("No video paths provided for merging")

    output_filename = f"merged_{uuid.uuid4()}.mp4"
    output_path = os.path.join(output_dir, output_filename)

    logger.info(f"Merging {len(video_paths)} videos into {output_path}")

    try:
        # Create input streams
        inputs = [ffmpeg.input(path) for path in video_paths]
        
        # Determine if we should use unsafe standard concat or complex filter
        # Complex filter is safer against diff resolutions/formats
        # stream = ffmpeg.concat(*inputs, v=1, a=1)
        
        # NOTE: If some videos differ in audio streams (none vs some), basic concat fails.
        # But for 'standard' usage, we assume uniformity. 
        # Robust method:
        # ffmpeg.concat(*inputs, v=1, a=1).output(output_path).run()
        
        # Let's try the safer re-encoding approach
        (
            ffmpeg
            .concat(*inputs, v=1, a=1)
            .output(output_path, vcodec='libx264', acodec='aac')
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )
        
        return output_path

    except ffmpeg.Error as e:
        logger.error(f"FFmpeg Error: {e.stderr.decode('utf8')}")
        raise RuntimeError("Video merging failed. Ensure files are valid video formats.")
