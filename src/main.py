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


def parse_command_line_arguments():
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
                        help="Maximal number of videos to download and convert in parallel. Defaults to 3. Optional.")

    parser.add_argument("-c", "--config_file", type=Path,
                        help="Path to a config file. Command line arguments take priority over the config file. Optional.")
    return parser.parse_args()


def load_config_file(args: argparse.Namespace):
    cfg = {}
    if args.config_file:
        if not os.path.isfile(args.config_file):
            raise argparse.ArgumentTypeError("The supplied CONFIG_FILE does not exist.")
        with open(args.config_file, "r") as config_file:
            cfg = yaml.load(config_file, Loader=yaml.SafeLoader)
    return cfg


def parse_destination_folder(args: argparse.Namespace, cfg) -> Path:
    destination_folder_path = None
    if 'Output-Folder' in cfg:
        destination_folder_path = Path(cfg['Output-Folder'])
    if args.output_folder:
        destination_folder_path = args.output_folder
    if not os.path.isdir(destination_folder_path):
        raise argparse.ArgumentTypeError("The supplied OUTPUT_FOLDER is invalid")
    return destination_folder_path


def parse_tmp_folder(args: argparse.Namespace, cfg) -> Path:
    tmp_directory = None
    if 'Temp-Dir' in cfg:
        tmp_directory = Path(cfg['Temp-Dir'])
    if args.temp_dir:
        tmp_directory = args.temp_dir
    if tmp_directory and not os.path.isdir(tmp_directory):
        raise argparse.ArgumentTypeError("The supplied TEMP_DIR is invalid")
    if not tmp_directory:
        tmp_directory = Path(tempfile.gettempdir(), "tum_video_scraper")  # default: (/tmp/tum_video_scraper/)
    if not os.path.isdir(tmp_directory):
        os.mkdir(tmp_directory)  # create temporary work-directory if it does not exist
    return tmp_directory


def parse_tum_live_subjects(args: argparse.Namespace, cfg) -> dict[str, (str, str)]:
    tum_live_subjects: dict[str, (str, str)] = {}
    if 'TUM-live' in cfg:
        tum_live_subjects.update(
            {key: parse_tum_live_subject_identifier(value) for key, value in cfg['TUM-live'].items()})
    if args.tum_live:
        tum_live_subjects.update({a: (b, c) for a, b, c in args.tum_live})
    return tum_live_subjects


def parse_panopto_folders(args: argparse.Namespace, cfg) -> dict[str, str]:
    panopto_folders: dict[str, str] = {}
    if 'Panopto' in cfg:
        panopto_folders.update(cfg['Panopto'])
    if args.panopto:
        panopto_folders.update({a: b for a, b in args.panopto})
    return panopto_folders


def parse_maximum_parallel_downloads(args: argparse.Namespace, cfg) -> Semaphore:
    maximum_parallel_downloads = 3
    if 'Maximum-Parallel-Downloads' in cfg:
        maximum_parallel_downloads = cfg['Maximum-Parallel-Downloads']
    if args.maximum_parallel_downloads:
        maximum_parallel_downloads = args.maximum_parallel_downloads
    # Keeps us from using massive amounts of RAM
    return Semaphore(maximum_parallel_downloads)


def parse_username_password(args: argparse.Namespace, cfg) -> (str | None, str | None):
    username = args.username or cfg.get('Username')
    password = args.password or cfg.get('Password')

    # Allows setting the password from stdin
    if username and not password:
        password = input("Please enter your TUM-Password (must fit to the TUM-Username):\n")

    return username, password


def parse_arguments():
    args = parse_command_line_arguments()
    cfg = load_config_file(args)

    tum_live_subjects = parse_tum_live_subjects(args, cfg)
    panopto_folders = parse_panopto_folders(args, cfg)

    destination_folder_path = parse_destination_folder(args, cfg)
    tmp_folder_path = parse_tmp_folder(args, cfg)

    semaphore = parse_maximum_parallel_downloads(args, cfg)

    (username, password) = parse_username_password(args, cfg)

    return tum_live_subjects, panopto_folders, destination_folder_path, tmp_folder_path, semaphore, username, password


def main():
    # We are a friendly background process
    os.nice(15)

    # Parse arguments
    tum_live_subjects, \
        panopto_folders, \
        destination_folder_path, \
        tmp_folder_path, \
        semaphore, \
        username, \
        password = parse_arguments()

    print("Starting new run!")

    # subject_folder_name -> [(episode_name, playlist_m3u8_URL)]
    videos_for_subject: dict[str, [(str, str)]] = {}

    # Scrape TUM-live videos
    if tum_live_subjects:
        print("\nScanning TUM-live:")
        tum_live.get_subjects(tum_live_subjects, username, password, videos_for_subject)

    # Scrape Panopto videos
    if panopto_folders:
        print("\nScanning Panopto:")
        panopto.get_folders(panopto_folders, username, password, videos_for_subject)

    # Download videos
    print("\n--------------------\n")
    print("Starting downloads:")
    for subject, playlists in videos_for_subject:
        subject_folder = Path(destination_folder_path, subject)
        subject_folder.mkdir(exist_ok=True)
        downloader.download_list_of_videos(playlists, subject_folder, tmp_folder_path, semaphore)


if __name__ == '__main__':
    main()
