import ffmpeg
import os
import uuid
import logging

logger = logging.getLogger(__name__)

def merge_videos(video_paths, output_dir):
    """
    Merges multiple video files into a single video file using FFmpeg.
    Handles modification of input streams to ensure every segment has video+audio
    before concatenation to prevent errors with silent clips.
    """
    if not video_paths:
        raise ValueError("No video paths provided for merging")

    output_filename = f"merged_{uuid.uuid4()}.mp4"
    output_path = os.path.join(output_dir, output_filename)

    logger.info(f"Merging {len(video_paths)} videos into {output_path}")

    try:
        streams_to_concat = []
        
        for path in video_paths:
            # 1. Probe the file to check for audio streams
            try:
                probe = ffmpeg.probe(path)
                video_stream_info = next((s for s in probe['streams'] if s['codec_type'] == 'video'), None)
                audio_stream_info = next((s for s in probe['streams'] if s['codec_type'] == 'audio'), None)
                
                if not video_stream_info:
                    logger.warning(f"File {path} has no video stream. Skipping.")
                    continue

                duration = float(video_stream_info.get('duration', probe['format']['duration']))
                
                # Input node
                inp = ffmpeg.input(path)
                
                v_stream = inp['v']
                
                if audio_stream_info:
                    a_stream = inp['a']
                else:
                    # Create silent audio match for video duration
                    logger.info(f"Adding silent audio to {path} (Duration: {duration}s)")
                    a_stream = ffmpeg.input('anullsrc', f='lavfi', t=duration).audio

                streams_to_concat.append(v_stream)
                streams_to_concat.append(a_stream)
                
            except Exception as probe_err:
                logger.error(f"Failed to probe {path}: {probe_err}")
                raise RuntimeError(f"Could not analyze video file: {os.path.basename(path)}")

        if not streams_to_concat:
            raise RuntimeError("No valid video streams found to merge.")

        # 2. Concat
        # We pass pairs of (v, a) for each input. Total inputs = len(streams_to_concat)/2
        # v=1, a=1 means we want 1 combined video and 1 combined audio track output.
        (
            ffmpeg
            .concat(*streams_to_concat, v=1, a=1)
            .output(output_path, vcodec='libx264', acodec='aac', pix_fmt='yuv420p', shortest=None)
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )
        
        return output_path

    except ffmpeg.Error as e:
        error_msg = e.stderr.decode('utf8') if e.stderr else str(e)
        logger.error(f"FFmpeg Error: {error_msg}")
        raise RuntimeError(f"Video merging failed: {error_msg}")
