import re
import subprocess
import sys
import time
from multiprocessing import Process, Semaphore
from pathlib import Path


def download_list_of_videos(videos: [(str, str)], output_folder_path: Path, tmp_directory: Path, semaphore: Semaphore):
    for filename, url in videos:
        filename = re.sub('[\\\\/:*?"<>|]|[\x00-\x20]', '_', filename) + ".mp4"  # Filter illegal filename chars
        output_file_path = Path(output_folder_path, filename)
        """We use locks to prevent processing the same video twice (e.g. if we run in multiple independent instances)"""
        """Locks can also be created by the user to keep us from downloading a specific video"""
        if not (Path(output_file_path.as_posix() + ".lock").exists()  # Check if lock file exists
                or output_file_path.exists()):  # Check if file exists (we downloaded and converted it already)
            Path(output_file_path.as_posix() + ".lock").touch()  # Create lock file
            Process(target=download_and_cut_video,  # Download video in separate process
                    args=(filename, url, output_file_path, tmp_directory, semaphore)).start()


def download_and_cut_video(filename: str, playlist_url: str, output_file_path: Path, tmp_directory: Path,
                           semaphore: Semaphore):
    semaphore.acquire()  # Acquire lock

    temporary_path = Path(tmp_directory, filename + ".original")  # Download location
    download_start_time = time.time()  # Track download time

    print(f"Download of {filename} started")
    ffmpeg = subprocess.run([
        'ffmpeg',
        '-y',  # Overwrite output file if it already exists
        '-hwaccel', 'auto',  # Hardware acceleration
        '-i', playlist_url,  # Input file
        '-c', 'copy',  # Codec name
        '-f', 'mp4',  # Force mp4 as output file format
        temporary_path  # Output file
    ], capture_output=True)

    if ffmpeg.returncode != 0:  # Print debug output in case of error
        print(f'Error during download of "{filename}" with ffmpeg:', file=sys.stderr)
        print(f'Playlist file: {playlist_url}', file=sys.stderr)
        print(f'Designated download location: {temporary_path}', file=sys.stderr)
        print(f'Designated output location: {output_file_path}', file=sys.stderr)
        print(f'Output of ffmpeg to stdout:\n' + ffmpeg.stdout.decode('utf-8'), file=sys.stderr)
        print(f'Output of ffmpeg to stderr:\n' + ffmpeg.stderr.decode('utf-8'), file=sys.stderr)
        return

    print(f"Download of {filename} completed after {(time.time() - download_start_time):.0f}s")
    conversion_start_time = time.time()  # Track auto-editor time
    print(f"Conversion of {filename} started")

    auto_editor = subprocess.run([
        'auto-editor',
        temporary_path,  # Input file
        '--silent_speed', '8',  # Speed multiplier while there is no audio
        '--video_codec', 'libx264',  # Video codec
        '--constant_rate_factor', '30',  # Framerate
        '--no_open',  # Don't open the finished file
        '-o', output_file_path  # Output file
    ], capture_output=True)

    if auto_editor.returncode != 0:  # Print debug output in case of error
        print(f'Error during conversion of "{filename}" with auto-editor:', file=sys.stderr)
        print(f'Playlist file: {playlist_url}', file=sys.stderr)
        print(f'Reading from: {temporary_path}', file=sys.stderr)
        print(f'Designated output location: {output_file_path}', file=sys.stderr)
        print(f'Output of auto-editor to stdout:\n' + ffmpeg.stdout.decode('utf-8'), file=sys.stderr)
        print(f'Output of auto-editor to stderr:\n' + ffmpeg.stderr.decode('utf-8'), file=sys.stderr)
        return

    print(f"Conversion of {filename} completed after {(time.time() - conversion_start_time):.0f}s")
    temporary_path.unlink()  # Delete original file
    Path(output_file_path.as_posix() + ".lock").unlink()  # Remove lock file
    print(f"Completed {filename} after {(time.time() - download_start_time):.0f}s")

    semaphore.release()  # Release lock
