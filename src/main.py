import argparse
import os
import tempfile
from multiprocessing import Semaphore
from pathlib import Path

import yaml

import downloader
import panopto
import tum_live


def parse_tum_live_subject(s: str) -> (str, str, str):
    try:
        a, b, c = s.split(':')
        if c and (c != "COMB" and c != "PRES" and c != "CAM"):
            raise argparse.ArgumentTypeError("Camera type must be \"COMB\", \"PRES\" or \"CAM\"")
        return a, b, c
    except ValueError:
        raise argparse.ArgumentTypeError("Subjects must be in the form: subject_name:subject_identifier:camera_type")


def parse_tum_live_subject_identifier(s: str) -> (str, str):
    try:
        a, b = s.split(':')
        if b and (b != "COMB" and b != "PRES" and b != "CAM"):
            raise argparse.ArgumentTypeError("Camera type must be \"COMB\", \"PRES\" or \"CAM\"")
        return a, b
    except ValueError:
        raise argparse.ArgumentTypeError(
            "Subjects must be in the form: \"Subject Name\": \"subject_identifier:camera_type\"")


def parse_tum_panopto_folder(s: str) -> (str, str):
    try:
        a, b = s.split(':')
        return a, b
    except ValueError:
        raise argparse.ArgumentTypeError("Panopto folders must be in the form: subject_name:panopto_folder_id")


if __name__ == '__main__':
    os.nice(15)  # set our nice value, so we can work in the background

    # Define command line arguments
    parser = argparse.ArgumentParser(description="Download and jump-cut TUM-Lecture-Videos")
    parser.add_argument("--tum_live",
                        help="List of TUM-live subjects in the form: subject_name:course_signature:camera_view",
                        type=parse_tum_live_subject, nargs='+')
    parser.add_argument("--panopto",
                        help="List of TUM-Panopto folders in the form: subject_name:panopto_folder_id",
                        type=parse_tum_panopto_folder, nargs='+')

    parser.add_argument("-u", "--username", help="TUM-Username (go42tum)", type=str)
    parser.add_argument("-p", "--password", help="TUM-Password (must fit to the TUM-Username)", type=str)

    parser.add_argument("-o", "--output_folder", type=Path,
                        help="Path to the output folder. Downloaded and converted videos get saved here.")

    parser.add_argument("-t", "--temp_dir",
                        help="Path for temporary files. Defaults to the system specific tmp folder. Optional.")
    parser.add_argument("-d", "--maximum_parallel_downloads", type=int,
                        help="Maximal number of videos to download and convert in parallel. "
                             "Defaults to 3. Optional.")

    parser.add_argument("-c", "--config_file", type=Path,
                        help="Path to a config file. "
                             "Command line arguments take priority over the config file. Optional.")
    args = parser.parse_args()

    # Load the config file (if there is one)
    if args.config_file:
        if not os.path.isfile(args.config_file):
            raise argparse.ArgumentTypeError("The supplied CONFIG_FILE does not exist.")
        with open(args.config_file, "r") as config_file:
            cfg = yaml.load(config_file, Loader=yaml.SafeLoader)

    # Parse the destination folder
    destination_folder_path = None
    if cfg and 'Output-Folder' in cfg:
        destination_folder_path = Path(cfg['Output-Folder'])
    if args.output_folder:
        destination_folder_path = args.output_folder
    if not os.path.isdir(destination_folder_path):
        raise argparse.ArgumentTypeError("The supplied OUTPUT_FOLDER is invalid")

    # Parse the tmp folder
    tmp_directory = None
    if cfg and 'Temp-Dir' in cfg:
        tmp_directory = Path(cfg['Temp-Dir'])
    if args.temp_dir:
        tmp_directory = args.temp_dir
    if tmp_directory and not os.path.isdir(tmp_directory):
        raise argparse.ArgumentTypeError("The supplied TEMP_DIR is invalid")
    if not tmp_directory:
        tmp_directory = Path(tempfile.gettempdir(), "tum_video_scraper")  # default: (/tmp/tum_video_scraper/)
    if not os.path.isdir(tmp_directory):
        os.mkdir(tmp_directory)  # create temporary work-directory if it does not exist

    # Parse tum-live subjects
    tum_live_subjects = {}
    if cfg and 'TUM-live' in cfg:
        tum_live_subjects.update(
            {key: parse_tum_live_subject_identifier(value) for key, value in cfg['TUM-live'].items()})
    if args.tum_live:
        tum_live_subjects.update({a: (b, c) for a, b, c in args.tum_live})

    # Parse panopto folders
    panopto_folders = {}
    if cfg and 'Panopto' in cfg:
        panopto_folders.update(cfg['Panopto'])
    if args.panopto:
        panopto_folders.update({a: b for a, b in args.panopto})

    # Parse username
    username = None
    if cfg and 'Username' in cfg:
        username = cfg['Username']
    if args.username:
        username = args.username

    # Parse password
    password = None
    if cfg and 'Password' in cfg:
        password = cfg['Password']
    if args.password:
        password = args.password

    # Check that we have username and password
    if username and not password:  # Allows setting the password from stdin
        password = input("Please enter your TUM-Password (must fit to the TUM-Username):\n")
    if not username or not password:
        raise argparse.ArgumentTypeError("TUM username and password required")

    # Parse maximum amount of parallel downloads
    maximum_parallel_downloads = 3
    if cfg and 'Maximum-Parallel-Downloads' in cfg:
        maximum_parallel_downloads = cfg['Maximum-Parallel-Downloads']
    if args.maximum_parallel_downloads:
        maximum_parallel_downloads = args.maximum_parallel_downloads
    semaphore = Semaphore(maximum_parallel_downloads)  # Keeps us from using massive amounts of RAM

    print("Starting new run!")
    videos_for_subject: [str, (str, str)] = []

    # Scrape TUM-live videos
    print("\nScanning TUM-live:")
    if tum_live_subjects:
        tum_live.get_subjects(tum_live_subjects, username, password, videos_for_subject)

    # Scrape Panopto videos
    print("\nScanning Panopto:")
    if panopto_folders:
        panopto.get_folders(panopto_folders, username, password, videos_for_subject)

    # Download videos
    print("\n--------------------\n")
    print("Starting downloads:")
    for subject, playlists in videos_for_subject:
        subject_folder = Path(destination_folder_path, subject)
        subject_folder.mkdir(exist_ok=True)
        downloader.download_list_of_videos(playlists, subject_folder, tmp_directory, semaphore)
