import argparse
import os
import tempfile
from pathlib import Path

import panopto
import tum_live


def parse_tum_live_subject(s: str) -> (str, str, str):
    try:
        a, b, c = s.split(':')
        if c != "COMB" and c != "PRES" and c != "CAM":
            raise argparse.ArgumentTypeError("Camera type must be \"COMB\", \"PRES\" or \"CAM\"")
        return a, b, c
    except ValueError:
        raise argparse.ArgumentTypeError("Subjects must be in the form: subject_name:subject_identifier:camera_type")


def parse_tum_panopto_folder(s: str) -> (str, str):
    try:
        a, b = s.split(':')
        return a, b
    except ValueError:
        raise argparse.ArgumentTypeError("Panopto folders must be in the form: subject_name:panopto_folder_id")


if __name__ == '__main__':
    os.nice(15)  # set our nice value, so we can work in the background

    TMP_DIRECTORY = Path(tempfile.gettempdir(), "tum_video_scraper")  # default: (/tmp/tum_video_scraper/)

    parser = argparse.ArgumentParser(description="Download and jump-cut TUM-Lecture-Videos")
    parser.add_argument("output_folder", help="output folder path", type=Path)
    parser.add_argument("-t", "--temp_dir", help="path for temporary files")
    parser.add_argument("--tum_live",
                        help="list of TUM-live subjects in the form: subject_name:subject_identifier:camera_type",
                        type=parse_tum_live_subject, nargs='+')
    parser.add_argument("--panopto",
                        help="list of TUM-Panopto folders in the form: subject_name:panopto_folder_id",
                        type=parse_tum_panopto_folder, nargs='+')
    parser.add_argument("-u", "--username", help="TUM-Username (go42tum)", type=str)
    parser.add_argument("-p", "--password", help="TUM-Password (must fit to the TUM-Username)", type=str)
    args = parser.parse_args()

    destination_folder_path: Path = args.output_folder
    if not destination_folder_path.is_dir():
        raise argparse.ArgumentTypeError("The supplied OUTPUT_FOLDER is invalid")
    if args.temp_dir:
        TMP_DIRECTORY = args.temp_dir
        if not os.path.isdir(TMP_DIRECTORY):
            raise argparse.ArgumentTypeError("The supplied TEMP_DIR is invalid")

    tum_live_subjects = args.tum_live
    panopto_folders = args.panopto
    username = args.username
    password = args.password

    if not os.path.isdir(TMP_DIRECTORY):  # create temporary work-directory if it does not exist
        os.mkdir(TMP_DIRECTORY)

    if panopto_folders and not (username and password):
        raise argparse.ArgumentTypeError("Panopto requires a TUM username and password")

    if tum_live_subjects:
        tum_live.get_subjects(tum_live_subjects, destination_folder_path, TMP_DIRECTORY)

    if panopto_folders:
        panopto.get_folders(panopto_folders, destination_folder_path, TMP_DIRECTORY, username, password)
