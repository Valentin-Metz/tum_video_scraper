import os
import re
import time
from multiprocessing import Process, Semaphore
from pathlib import Path


def download_list_of_videos(videos: (str, str), output_folder_path: Path, tmp_directory: Path, semaphore: Semaphore):
    for filename, url in videos:
        filename = re.sub('[\\\\/:*?"<>|]|[\x00-\x20]', '_', filename) + ".mp4"
        output_file_path = Path(output_folder_path, filename)
        """We use locks to prevent processing the same video twice (for example if we run as a daemon)
        Locks can also be created by the user to keep us from downloading a specific video"""
        if not (Path(output_file_path.as_posix() + ".lock").exists()  # check if lock exists
                or output_file_path.exists()):  # check if file exists
            Path(output_file_path.as_posix() + ".lock").touch()  # create lock
            """We use one process for every video"""
            Process(target=download_and_cut_video,
                    args=(filename, url, output_file_path, tmp_directory, semaphore)).start()


def download_and_cut_video(filename: str, playlist_url: str, output_file_path: Path, tmp_directory: Path,
                           semaphore: Semaphore):
    semaphore.acquire()
    temporary_path = Path(tmp_directory, filename + ".original")
    download_command = "ffmpeg -y -hide_banner -hwaccel auto " + \
                       f"-i \"{playlist_url}\" -c copy -f mp4 \"{temporary_path}\" > /dev/null"
    print("Starting download of " + filename)
    download_start_time = time.time()
    os.system(download_command)
    print(f"Download of {filename} completed after {str(time.time() - download_start_time)}s")
    cut_command = f"auto-editor \"{temporary_path}\" --silent_speed 8 " \
                  f"--video_codec libx264 --constant_rate_factor 30 --no_open -o \"{output_file_path}\" > /dev/null"
    conversion_start_time = time.time()
    os.system(cut_command)
    print(f"Conversion of {filename} completed after {str(time.time() - conversion_start_time)}s")
    temporary_path.unlink()
    Path(output_file_path.as_posix() + ".lock").unlink()  # remove lock
    semaphore.release()
    print(f"Done with {filename} after {str(time.time() - download_start_time)}s")
