import re
import shutil
import subprocess
import sys
import time
from multiprocessing import Process, Semaphore
from pathlib import Path


def download_list_of_videos(videos: [(str, str)],
                            output_folder_path: Path, tmp_directory: Path,
                            keep_original: bool, jump_cut: bool,
                            semaphore: Semaphore):
    children = []
    for filename, url in videos:
        filename = re.sub('[\\\\/:*?"<>|]|[\x00-\x20]', '_', filename) + ".mp4"  # Filter illegal filename chars
        output_file_path = Path(output_folder_path, filename)
        output_file_path_jc = Path(re.sub(r'\.(?=[^.]*$)', '_jc.', output_file_path.as_posix()))  # Add _jc to filename
        """We use locks to prevent processing the same video twice (e.g. if we run in multiple independent instances)"""
        """Locks can also be created by the user to keep us from downloading a specific video"""
        if not (Path(output_file_path.as_posix() + ".lock").exists()  # Check if lock file exists
                or output_file_path.exists()
                or output_file_path_jc.exists()):  # Check if file exists (we downloaded and converted it already)
            Path(output_file_path.as_posix() + ".lock").touch()  # Create lock file
            child = Process(target=download,  # Download video in separate process
                    args=(filename, url,
                          output_file_path, output_file_path_jc, tmp_directory,
                          keep_original, jump_cut,
                          semaphore))
            child.start()
            children.append(child)
    return children


def download(filename: str, playlist_url: str,
             output_file_path: Path, output_file_path_jc: Path, tmp_directory: Path,
             keep_original: bool, jump_cut: bool,
             semaphore: Semaphore):
    print(f"Download of {filename} started")
    semaphore.acquire()  # Acquire lock
    download_start_time = time.time()  # Track download time
    temporary_path = Path(tmp_directory, filename + ".original")  # Download location
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
        print(f"Error during download of \"{filename}\" with ffmpeg:", file=sys.stderr)
        print(f"Playlist file: {playlist_url}", file=sys.stderr)
        print(f"Designated download location: {temporary_path}", file=sys.stderr)
        print(f"Designated output location: {output_file_path}", file=sys.stderr)
        print(f"Output of ffmpeg to stdout:\n{ffmpeg.stdout.decode('utf-8')}", file=sys.stderr)
        print(f"Output of ffmpeg to stderr:\n{ffmpeg.stderr.decode('utf-8')}", file=sys.stderr)
        return

    print(f"Download of {filename} completed after {(time.time() - download_start_time):.0f}s")
    if keep_original:
        shutil.copy2(temporary_path, output_file_path)  # Copy original file to output location
    if jump_cut:
        cut_video(filename, playlist_url,
                  output_file_path, output_file_path_jc, temporary_path,
                  download_start_time,
                  semaphore)
    else:
        temporary_path.unlink()  # Delete original file
        Path(output_file_path.as_posix() + ".lock").unlink()  # Remove lock file
        print(f"Completed {filename} after {(time.time() - download_start_time):.0f}s")

        semaphore.release()  # Release lock


def cut_video(filename: str, playlist_url: str,
              output_file_path: Path, output_file_path_jc: Path, input_path: Path,
              download_start_time: float,
              semaphore: Semaphore):
    print(f"Conversion of {filename} started")
    conversion_start_time = time.time()  # Track auto-editor time
    auto_editor = subprocess.run([
        'auto-editor',
        input_path,  # Input file
        '--silent_speed', '8',  # Speed multiplier while there is no audio
        '--video_codec', 'h264',  # Video codec
        '--no_open',  # Don't open the finished file
        '-o', output_file_path_jc  # Output file
    ], capture_output=True)

    if auto_editor.returncode != 0:  # Print debug output in case of error
        print(f"Error during conversion of \"{filename}\" with auto-editor:", file=sys.stderr)
        print(f"Playlist file: {playlist_url}", file=sys.stderr)
        print(f"Reading from: {input_path}", file=sys.stderr)
        print(f"Designated output location: {output_file_path_jc}", file=sys.stderr)
        print(f"Output of auto-editor to stdout:\n{auto_editor.stdout.decode('utf-8')}", file=sys.stderr)
        print(f"Output of auto-editor to stderr:\n{auto_editor.stderr.decode('utf-8')}", file=sys.stderr)
        return

    print(f"Conversion of {filename} completed after {(time.time() - conversion_start_time):.0f}s")
    input_path.unlink()  # Delete original file
    Path(output_file_path.as_posix() + ".lock").unlink()  # Remove lock file
    print(f"Completed {filename} after {(time.time() - download_start_time):.0f}s")

    semaphore.release()  # Release lock
